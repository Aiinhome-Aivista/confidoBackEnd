# import os
# import uuid
# import json
# import asyncio
# import platform
# import subprocess
# import edge_tts
# from pydub import AudioSegment, utils
# from pydub.utils import mediainfo
# from googletrans import Translator

# # Initialize translator
# translator = Translator()

# # Base URL for the API
# BASE_URL = "http://122.163.121.176:3029" 

# # Voice mapping for avatars
# VOICE_MAP = {
#     1: {  # ravi
#         "english": "en-IN-PrabhatNeural",
#         "hindi": "hi-IN-MadhurNeural",
#         "bengali": "bn-IN-TanishaaNeural",
#         "french": "fr-FR-HenriNeural"
#     },
#     2: {  # hema
#         "english": "en-US-JennyNeural",
#         "hindi": "hi-IN-SwaraNeural",
#         "bengali": "bn-IN-TanishaaNeural",
#         "french": "fr-FR-DeniseNeural"
#     },
#     3: {  # subho
#         "english": "en-US-GuyNeural",
#         "hindi": "hi-IN-MadhurNeural",
#         "bengali": "bn-IN-TanishaaNeural",
#         "french": "fr-FR-HenriNeural"
#     },
#     4: {  # sita
#         "english": "en-IN-NeerjaNeural",
#         "hindi": "hi-IN-SwaraNeural",
#         "bengali": "bn-IN-TanishaaNeural",
#         "french": "fr-FR-DeniseNeural"
#     }
# }

# # Paths for static files
# STATIC_AUDIO_DIR = "static/audio"
# STATIC_LIPSYNC_DIR = "static/lipsync"
# os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
# os.makedirs(STATIC_LIPSYNC_DIR, exist_ok=True)

# # Detect OS
# SYSTEM = platform.system()
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# BIN_DIR = os.path.join(PROJECT_ROOT, "static", "bin")

# if SYSTEM == "Windows":
#     rhubarb_path = os.path.join(BIN_DIR, "rhubarb.exe")
#     ffmpeg_path = os.path.join(BIN_DIR, "ffmpeg.exe")
#     ffprobe_path = os.path.join(BIN_DIR, "ffprobe.exe")
# else:
#     rhubarb_path = os.path.join(BIN_DIR, "rhubarb")
#     ffmpeg_path = os.path.join(BIN_DIR, "ffmpeg")
#     ffprobe_path = os.path.join(BIN_DIR, "ffprobe")

# # Configure Pydub
# AudioSegment.converter = ffmpeg_path
# AudioSegment.ffprobe = ffprobe_path
# utils.get_prober_name = lambda: ffprobe_path

# os.environ["FFMPEG_BINARY"] = ffmpeg_path
# os.environ["FFPROBE_BINARY"] = ffprobe_path

# # ------------------- UTIL FUNCTIONS -------------------

# # Edge TTS
# async def _edge_speak(text, voice, filename):
#     communicate = edge_tts.Communicate(text=text, voice=voice)
#     await communicate.save(filename)  # outputs mp3

# def convert_mp3_to_ogg(mp3_file, ogg_file):
#     sound = AudioSegment.from_file(mp3_file, format="mp3")
#     sound.export(ogg_file, format="ogg")

# def get_voice_for_avatar(avatar_id, lang_name="english"):
#     lang_key = (lang_name or "english").strip().lower()
#     avatar_map = VOICE_MAP.get(int(avatar_id))
#     if isinstance(avatar_map, dict):    
#         return avatar_map.get(lang_key, avatar_map.get("english"))
#     return avatar_map.get(lang_key, avatar_map.get("english", "en-US-JennyNeural"))

# def generate_tts_audio(text, avatar_id, session_id, lang_name="english"):
#     unique_id = str(uuid.uuid4())
#     voice = get_voice_for_avatar(avatar_id, lang_name)

#     mp3_file = f"{STATIC_AUDIO_DIR}/response_{session_id}_{unique_id}.mp3"
#     asyncio.run(_edge_speak(text, voice, mp3_file))

#     ogg_file = f"{STATIC_AUDIO_DIR}/response_{session_id}_{unique_id}.ogg"
#     convert_mp3_to_ogg(mp3_file, ogg_file)

#     return mp3_file, ogg_file, unique_id

# def generate_lipsync_json(audio_filename, text, session_id, unique_id):
#     json_output = f"{STATIC_LIPSYNC_DIR}/response_{session_id}_{unique_id}_lipsync.json"
#     dialog_file = f"static/audio/dialog_{session_id}_{unique_id}.txt"
#     with open(dialog_file, "w", encoding="utf-8") as f:
#         f.write(text)

#     subprocess.run([
#         rhubarb_path,
#         audio_filename,
#         "-o", json_output,
#         "-d", dialog_file,
#         "-f", "json"
#     ], check=True)

#     info = mediainfo(audio_filename)
#     duration = float(info['duration'])

#     with open(json_output, "r+", encoding="utf-8") as f:
#         data = json.load(f)
#         data["metadata"] = {
#             "soundFile": audio_filename,
#             "duration": round(duration, 2)
#         }
#         f.seek(0)
#         json.dump(data, f, indent=2)
#         f.truncate()

#     os.remove(dialog_file)
#     return json_output

# def translate_text(text, lang):
#     try:
#         if not lang or not isinstance(lang, str):
#             return text
#         lang = lang.strip().lower()
#         if lang == "hindi":
#             return translator.translate(text, dest="hi").text
#         elif lang in ["bengali", "bangla"]:
#             return translator.translate(text, dest="bn").text
#         elif lang == "french":
#             return translator.translate(text, dest="fr").text
#         elif lang == "english":
#             return translator.translate(text, dest="en").text
#         return text
#     except Exception as e:
#         return f"[Translation failed: {str(e)}] {text}"
