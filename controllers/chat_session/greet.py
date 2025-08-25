import os
from flask import request, jsonify
from controllers.chat_session.chat import (
    BASE_URL,
    VOICE_MAP,
    STATIC_AUDIO_DIR,
    STATIC_LIPSYNC_DIR,
    generate_tts_audio,
    generate_lipsync_json,
    translate_text
)
from repositories.chat_repository import get_language_by_session

# static greeting template
STATIC_MESSAGE = (
    "Hello there! I'm {avatar_name}, your personal conversation partner. "
    "Here, we'll practice speaking, remove hesitation, and build your confidence step by step. "
    "Whatever you say, we'll do it with confidence!"
)

# greet controller to handle greeting requests
def greet_controller():
    try:
        data = request.get_json()
        avatar_name = data.get("avatarName")
        avatar_id = int(data.get("avatarId", 1))
        language_id = data.get("languageId")
        session_id = data.get("sessionId")

        if not language_id or not session_id:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "languageId and sessionId are required",
                "data": {}
            }), 400

        # 🔹 Get language name from DB using session
        session_info = get_language_by_session(session_id)
        lang_name = (session_info.get("language_name") or "english").strip().lower()

        # 🔹 Prepare greeting text
        raw_message = STATIC_MESSAGE.format(avatar_name=avatar_name)
        translated_message = translate_text(raw_message, lang_name)
        print(f"Translated Message: {translated_message}")

        # 🔹 Generate audio + lipsync JSON using chat.py utilities
        mp3_file, ogg_file, unique_id = generate_tts_audio(
            translated_message, avatar_id, session_id, lang_name
        )
        lipsync_file = generate_lipsync_json(
            ogg_file, translated_message, session_id, unique_id
        )

        # 🔹 Build response
        response = {
            "data": {
                "avatarId": avatar_id,
                "message": translated_message,
                "sessionId": session_id,
                "audio_url": f"{BASE_URL}/audio/{os.path.basename(mp3_file)}",
                "lipsync_url": f"{BASE_URL}/lipsync/{os.path.basename(lipsync_file)}"
            },
            "message": "Greetings generated successfully.",
            "status": "success",
            "statusCode": 200
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": f"Error generating greeting: {str(e)}",
            "data": {}
        }), 500
