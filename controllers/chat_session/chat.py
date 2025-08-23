import os
import re
import uuid
import json
import asyncio
import platform
import edge_tts
import subprocess
from pydub import AudioSegment
from pydub.utils import mediainfo
from flask import jsonify, request
from models.mistral_client import call_mistral
from sessions.session_store import save_chat_history
from repositories.chat_repository import get_language_by_session, save_communication_history
from sessions.session_manager import add_message, get_history, is_session_active, session_exists, start_session
from googletrans import Translator

# Initialize translator
translator = Translator()

# Base URL for the API
BASE_URL = "http://122.163.121.176:3029" 

# Voice mapping for avatars
VOICE_MAP = {
    1: "en-IN-PrabhatNeural",   # Ravi → male
    2: "en-US-JennyNeural",     # Hema → female
    3: "en-US-GuyNeural",       # Subho → male
    4: "en-IN-NeerjaNeural"     # Sita → female
}

# Paths for static files
STATIC_AUDIO_DIR = "static/audio"
STATIC_LIPSYNC_DIR = "static/lipsync"
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
os.makedirs(STATIC_LIPSYNC_DIR, exist_ok=True)

# Detect OS
SYSTEM = platform.system()

# Base path where Rhubarb is stored
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_DIR = os.path.join(PROJECT_ROOT, "static", "bin")

# Get the path to rhubarb.exe or rhubarb binary
if SYSTEM == "Windows":
    rhubarb_path = os.path.join(BIN_DIR, "rhubarb.exe")
else:
    rhubarb_path = os.path.join(BIN_DIR, "rhubarb")

# Verify rhubarb path
print("Resolved rhubarb path:", rhubarb_path, "Exists?", os.path.isfile(rhubarb_path))

# generate TTS audio using Edge TTS
async def _edge_speak(text, voice, filename):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(filename)  # outputs mp3

# Convert MP3 to OGG for Rhubarb lip-sync
def convert_mp3_to_ogg(mp3_file, ogg_file):
    """Convert TTS MP3 to OGG for Rhubarb."""
    sound = AudioSegment.from_file(mp3_file, format="mp3")
    sound.export(ogg_file, format="ogg")

# generate TTS audio and return OGG file path with unique ID
def generate_tts_audio(text, avatar_id, session_id):
    unique_id = str(uuid.uuid4())  # unique per message
    voice = VOICE_MAP.get(avatar_id, "en-US-JennyNeural")

    mp3_file = f"{STATIC_AUDIO_DIR}/response_{session_id}_{unique_id}.mp3"
    asyncio.run(_edge_speak(text, voice, mp3_file))

    # Optionally also generate OGG for Rhubarb
    ogg_file = f"{STATIC_AUDIO_DIR}/response_{session_id}_{unique_id}.ogg"
    convert_mp3_to_ogg(mp3_file, ogg_file)

    # DO NOT remove mp3_file
    return mp3_file, ogg_file, unique_id

# Rhubarb lip-sync JSON
def generate_lipsync_json(audio_filename, text, session_id, unique_id):
    json_output = f"{STATIC_LIPSYNC_DIR}/response_{session_id}_{unique_id}_lipsync.json"

    # Write dialogue to temp file
    dialog_file = f"static/audio/dialog_{session_id}_{unique_id}.txt"
    with open(dialog_file, "w", encoding="utf-8") as f:
        f.write(text)

    # Run Rhubarb
    subprocess.run([
        rhubarb_path,
        audio_filename,
        "-o", json_output,
        "-d", dialog_file,
        "-f", "json"
    ], check=True)

    # Add metadata: audio path + duration
    info = mediainfo(audio_filename)
    duration = float(info['duration'])

    with open(json_output, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["metadata"] = {
            "soundFile": audio_filename,
            "duration": round(duration, 2)
        }
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    os.remove(dialog_file)
    return json_output

# Translate text to Hindi or Bengali if needed
def translate_text(text, lang):
    try:
        if not lang or not isinstance(lang, str):
            return text
        lang = lang.strip().lower()
        if lang == "hindi":
            return translator.translate(text, dest="hi").text
        elif lang in ["bengali", "bangla"]:
            return translator.translate(text, dest="bn").text
        return text
    except Exception as e:
        return f"[अनुवाद/অনুবাদ विफল: {str(e)}] {text}"

# Chat controller for handling chat requests
def chat_controller():
    data = request.get_json()
    session_id  = data.get("session_id")
    print("session_id",session_id)
    time_limit  = data.get("time")
    user_input  = data.get("user_input", "").strip()
    avatar_id   = int(data.get("avatar_id", 1))

    if not session_id or not time_limit:
        return jsonify({"status":"failed","statusCode":400,"message":"session_id and time are required","data":{}}),400

    matches = re.findall(r"\d+", str(time_limit))
    if not matches:
        return jsonify({"status":"failed","statusCode":400,"message":"Invalid time_limit format","data":{}}),400
    duration_minutes = int(matches[0])

    if not session_exists(session_id):
        start_session(session_id, duration_minutes)

    session_info = get_language_by_session(session_id)
    lang_name = (session_info.get("language_name") or "english").strip().lower()
    user_id   = session_info.get("user_id")

    if not is_session_active(session_id):
        return jsonify({
            "status":"success","statusCode":200,
            "message":translate_text("⏳ Time is up. Thank you for the discussion!", lang_name),
            "data":{"end":True}
        }),200

    # Generate AI response 
    if user_input == "":
        prompt = ("You are starting a communication session.\n"
                  "Greet the user and ask the first question. Be friendly and concise.\n"
                  "Important: Do NOT use emojis or special symbols in your response.")
    else:
        history = get_history(session_id)
        print("history:", history)
        formatted = [f"{m['role'].capitalize()}: {m['message']}" for m in history[-6:]]
        dialog    = "\n".join(formatted)
        print("dialog:", dialog)
        prompt = ("You are chatting with a user. Continue the conversation naturally.\n\n"
                  f"to  better understand the context of the query {history}\n\n"
                  f"here is the query {user_input} .only respond the query\n\n"
                  "Important: Do NOT use emojis or special symbols in your response.\n"
                  "Respond to keep the discussion flowing.")

    print(f"User input: {user_input}")
    
    # Call Mistral API
    raw_ai_response = call_mistral(prompt)
    print(f"Raw AI response: {raw_ai_response}")
    
    # translate text from english to hindi or bengali if needed
    translated_ai = translate_text(raw_ai_response, lang_name)
    # print(f"Translated AI response: {translated_ai}")

    # Save messages
    if user_input:
        add_message(session_id, "user", user_input)
    add_message(session_id, "ai", translated_ai)

    if user_input:
        history = get_history(session_id)
        
        # Save communication history
        save_communication_history(session_id, history, lang_name, user_id)
        
        # Save chat history
        save_chat_history(session_id, history)

    # Generate audio + lipsync JSON with UUID
    mp3_file, ogg_file, unique_id = generate_tts_audio(raw_ai_response, avatar_id, session_id)
    json_file = generate_lipsync_json(ogg_file, raw_ai_response, session_id, unique_id)

    return jsonify({
        "status": "success",
        "statusCode": 200,
        "message": "response sent" if user_input else "greeting sent",
        "data": {
            "session_id": session_id,
            "message": translated_ai,
            "audio_url": f"{BASE_URL}/audio/{os.path.basename(mp3_file)}",  
            "lipsync_url": f"{BASE_URL}/lipsync/{os.path.basename(json_file)}",
            "end": False
        }
    }), 200


