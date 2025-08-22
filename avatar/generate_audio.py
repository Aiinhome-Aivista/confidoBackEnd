import asyncio
import os
import subprocess
import json
import uuid
from pydub import AudioSegment
from pydub.utils import mediainfo
import edge_tts

# ------------------- Directory Setup -------------------
STATIC_AUDIO_DIR = "static/audio"
STATIC_LIPSYNC_DIR = "static/lipsync"
TOOLS_DIR = "tools"  # put rhubarb.exe here for simplicity

os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)
os.makedirs(STATIC_LIPSYNC_DIR, exist_ok=True)
os.makedirs(TOOLS_DIR, exist_ok=True)

# ------------------- Character → voice mapping -------------------
characters = {
    "ravi": "en-IN-PrabhatNeural",  # male
    "hema": "en-US-JennyNeural",  # female
    "subho": "en-US-GuyNeural",  # male
    "sita": "en-IN-NeerjaNeural",  # female
}

# ------------------- TTS Functions -------------------

# Generate TTS audio using Edge TTS
async def _edge_speak(text, voice, filename):
    """Generate TTS as MP3 using edge-tts"""
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(filename)

# Convert MP3 to OGG for Rhubarb lip-sync
def convert_mp3_to_ogg(mp3_file, ogg_file):
    """Convert MP3 → OGG for Rhubarb"""
    sound = AudioSegment.from_file(mp3_file, format="mp3")
    sound.export(ogg_file, format="ogg")

# Generate TTS audio and return OGG file path with unique ID
def generate_tts_audio(text, voice, character_name):
    """Generate MP3 + OGG audio for a character"""
    unique_id = str(uuid.uuid4())
    mp3_file = f"{STATIC_AUDIO_DIR}/{character_name}_{unique_id}.mp3"
    ogg_file = f"{STATIC_AUDIO_DIR}/{character_name}_{unique_id}.ogg"

    # Create MP3
    asyncio.run(_edge_speak(text, voice, mp3_file))
    print(f"🎵 Saved MP3: {mp3_file}")

    # Convert to OGG
    convert_mp3_to_ogg(mp3_file, ogg_file)
    print(f"🎵 Saved OGG: {ogg_file}")

    return mp3_file, ogg_file, unique_id

# ------------------- Rhubarb LipSync Functions -------------------

# Get the path to rhubarb.exe
def get_rhubarb_path():
    """
    Returns the path to rhubarb.exe.
    Priority:
      1. tools/rhubarb.exe (inside project)
      2. Hardcoded fallback path
    """
    local_path = os.path.join(TOOLS_DIR, "rhubarb.exe")
    fallback_path = r"C:\Rhubarb-Lip-Sync-1.14.0-Windows\rhubarb.exe"

    if os.path.exists(local_path):
        return local_path
    elif os.path.exists(fallback_path):
        return fallback_path
    else:
        raise FileNotFoundError(
            "❌ Rhubarb not found. Place rhubarb.exe in ./tools or update the fallback path."
        )

# Generate lipsync JSON using Rhubarb
def generate_lipsync_json(audio_filename, text, character_name, unique_id):
    """Run Rhubarb on OGG file and generate JSON with metadata"""
    json_output = f"{STATIC_LIPSYNC_DIR}/{character_name}_{unique_id}_lipsync.json"
    rhubarb_path = get_rhubarb_path()

    # Save spoken text to a dialog file
    dialog_file = f"{STATIC_AUDIO_DIR}/{character_name}_{unique_id}.txt"
    with open(dialog_file, "w", encoding="utf-8") as f:
        f.write(text)

    # Run rhubarb
    subprocess.run(
        [
            rhubarb_path,
            audio_filename,
            "-o",
            json_output,
            "-d",
            dialog_file,
            "-f",
            "json",
        ],
        check=True,
    )

    # Add metadata
    info = mediainfo(audio_filename)
    duration = float(info["duration"])

    with open(json_output, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["metadata"] = {"soundFile": audio_filename, "duration": round(duration, 2)}
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    os.remove(dialog_file)
    return json_output


# interactive function to run the script
def run_interactive():
    while True:
        print("\nAvailable characters:", ", ".join(characters.keys()))
        choice = input("👉 Choose a character (or type 'exit'): ").strip().lower()
        if choice == "exit":
            break
        if choice not in characters:
            print("❌ Invalid choice")
            continue

        voice = characters[choice]
        text = f"Hello there! I'm {choice.capitalize()}, your personal conversation partner. Here, we'll practice speaking, remove hesitation, and build your confidence—step by step. Whatever you say, we'll do it with confidence!"

        print(f"\n🎙 Generating for {choice}...")
        mp3_file, ogg_file, uid = generate_tts_audio(text, voice, choice)
        json_file = generate_lipsync_json(ogg_file, text, choice, uid)

        print(f"✅ Done!\nMP3: {mp3_file}\nOGG: {ogg_file}\nJSON: {json_file}")


# main entry point
if __name__ == "__main__":
    run_interactive()
    
