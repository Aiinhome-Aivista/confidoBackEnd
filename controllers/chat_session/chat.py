import os
import re
import uuid
import json
import asyncio
import platform
import edge_tts
import subprocess
from pydub.utils import mediainfo
from flask import jsonify, request
from pydub import AudioSegment, utils
from models.mistral_client import call_mistral
from sessions.session_store import save_chat_history
from repositories.chat_repository import get_language_by_session, save_communication_history
from sessions.session_manager import add_message, get_history, is_session_active, session_exists, start_session
from googletrans import Translator

# Initialize translator
translator = Translator()

# Base URL for the API
BASE_URL = "http://122.163.121.176:3029" 

# Voice mapping for avatars (Male / Female)
VOICE_MAP = {
    1: {  # Ravi (Male)
        "english": "en-IN-PrabhatNeural", 
        "hindi": "hi-IN-MadhurNeural",    
        "bengali": "bn-IN-BashkarNeural", 
        "french": "fr-FR-HenriNeural"       
    },
    2: {  # Hema (Female)
        "english": "en-US-JennyNeural",     
        "hindi": "hi-IN-SwaraNeural",       
        "bengali": "bn-IN-TanishaaNeural",  
        "french": "fr-FR-DeniseNeural"      
    },
    3: {  # Subho (Male)
        "english": "en-US-GuyNeural",     
        "hindi": "hi-IN-MadhurNeural",    
        "bengali": "bn-IN-BashkarNeural", 
        "french": "fr-FR-HenriNeural"     
    },
    4: {  # Sita (Female)
        "english": "en-IN-NeerjaNeural",    
        "hindi": "hi-IN-SwaraNeural",       
        "bengali": "bn-IN-TanishaaNeural",  
        "french": "fr-FR-DeniseNeural"      
    }
}

# Paths for static files
STATIC_AUDIO_DIR = "static/audio"
STATIC_LIPSYNC_DIR = "static/lipsync"
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
os.makedirs(STATIC_LIPSYNC_DIR, exist_ok=True)

# Detect OS
SYSTEM = platform.system()

# Base path where binaries are stored
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_DIR = os.path.join(PROJECT_ROOT, "static", "bin")

# Get the path to rhubarb.exe or rhubarb binary
if SYSTEM == "Windows":
    rhubarb_path = os.path.join(BIN_DIR, "rhubarb.exe")
    ffmpeg_path = os.path.join(BIN_DIR, "ffmpeg.exe")
    ffprobe_path = os.path.join(BIN_DIR, "ffprobe.exe")
else:
    rhubarb_path = os.path.join(BIN_DIR, "rhubarb")
    ffmpeg_path = os.path.join(BIN_DIR, "ffmpeg")
    ffprobe_path = os.path.join(BIN_DIR, "ffprobe")

# Force pydub to use bundled binaries
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

# Force mediainfo to use our ffprobe
utils.get_prober_name = lambda: ffprobe_path

# Also set env vars for safety
os.environ["FFMPEG_BINARY"] = ffmpeg_path
os.environ["FFPROBE_BINARY"] = ffprobe_path

# Verify paths
print("Resolved rhubarb path:", rhubarb_path, "Exists?", os.path.isfile(rhubarb_path))
print("Resolved ffmpeg path:", ffmpeg_path, "Exists?", os.path.isfile(ffmpeg_path))
print("Resolved ffprobe path:", ffprobe_path, "Exists?", os.path.isfile(ffprobe_path))

# generate TTS audio using Edge TTS
async def _edge_speak(text, voice, filename):
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(filename)  # outputs mp3

# Convert MP3 to OGG for Rhubarb lip-sync
def convert_mp3_to_ogg(mp3_file, ogg_file):
    """Convert TTS MP3 to OGG for Rhubarb."""
    sound = AudioSegment.from_file(mp3_file, format="mp3")
    sound.export(ogg_file, format="ogg")

# Get the correct voice based on avatar and language
def get_voice_for_avatar(avatar_id, lang_name="english"):
    """Return the correct voice based on avatar and session language."""
    lang_key = (lang_name or "english").strip().lower()
    avatar_map = VOICE_MAP.get(int(avatar_id))

     # dynamic multi-language mapping
    if isinstance(avatar_map, dict):    
        return avatar_map.get(lang_key, avatar_map.get("english"))

    # fallback to English if language not found
    return avatar_map.get(lang_key, avatar_map.get("english", "en-US-JennyNeural"))

# generate TTS audio and return OGG file path with unique ID
def generate_tts_audio(text, avatar_id, session_id, lang_name="english"):
    """Generate MP3 and OGG TTS audio based on avatar and language."""
    unique_id = str(uuid.uuid4())  # unique per message
    voice = get_voice_for_avatar(avatar_id, lang_name)

    mp3_file = f"{STATIC_AUDIO_DIR}/response_{session_id}_{unique_id}.mp3"
    asyncio.run(_edge_speak(text, voice, mp3_file))

    ogg_file = f"{STATIC_AUDIO_DIR}/response_{session_id}_{unique_id}.ogg"
    convert_mp3_to_ogg(mp3_file, ogg_file)

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

# Translate text to specified language
def translate_text(text, lang):
    try:
        if not lang or not isinstance(lang, str):
            return text
        lang = lang.strip().lower()
        if lang == "hindi":
            return translator.translate(text, dest="hi").text
        elif lang in ["bengali", "bangla"]:
            return translator.translate(text, dest="bn").text
        elif lang == "french":
            return translator.translate(text, dest="fr").text
        elif lang == "english":
            return translator.translate(text, dest="en").text
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
        lang_userInput=translate_text(user_input, lang="english")
        print("lang_userInput:", lang_userInput)
        prompt = ("You are chatting with a user. Continue the conversation naturally.\n\n"
                  f"to  better understand the context of the query {history}\n\n"
                  f"here is the query {lang_userInput} .only respond the query\n\n"
                  "Important: Do NOT use emojis or special symbols in your response.\n"
                  "Respond to keep the discussion flowing.")

    print(f"User input: {user_input}")
    
    # Call Mistral API
    raw_ai_response = call_mistral(prompt)
    print(f"Raw AI response: {raw_ai_response}")
    
    # translate text from english to hindi or bengali if needed
    translated_ai = translate_text(raw_ai_response, lang_name)
    print(f"Translated AI response: {translated_ai}")

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
    mp3_file, ogg_file, unique_id = generate_tts_audio(translated_ai, avatar_id, session_id, lang_name)
    json_file = generate_lipsync_json(ogg_file, translated_ai, session_id, unique_id)

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


