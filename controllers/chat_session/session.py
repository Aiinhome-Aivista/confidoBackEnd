from flask import request, jsonify
from repositories.session_create import create_session_model

# handle session creation
def session_controller():
    """
    Handles incoming POST request to create a new session.
    """
    try:
        data = request.get_json()

        # Validate if JSON body exists
        if not data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Request body is missing or invalid JSON.",
                "data": {}
            }), 400

        # Extract parameters from payload
        session_id = data.get("sessionId")
        user_id = data.get("userId")
        username = data.get("userName", "")
        language_id = data.get("languageId")
        avatar_id = data.get("avatarId")
        avatar_name = data.get("avatarName", "")

        # Check required fields
        required_fields = [session_id, user_id, language_id, avatar_id]
        if any(field in (None, "") for field in required_fields):
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Missing one or more required fields: sessionId, userId, languageId, avatarId.",
                "data": {}
            }), 400

        # Call the model function to insert into DB
        is_created = create_session_model(session_id, user_id, username, language_id, avatar_id, avatar_name)
        print(f"Session creation status: {is_created}")

        if is_created:
            return jsonify({
                "status": "success",
                "statusCode": 200,
                "message": "Session created successfully.",
                "data": {
                    "sessionId": session_id,
                    "userId": user_id,
                    "avatarId": avatar_id,
                    "message": f"Hello there! 👋 I'm {avatar_name}, your personal conversation partner. Here, we'll practice speaking, remove hesitation, and build your confidence—step by step. Whatever you say, we'll do it with confidence!"
                }
            }), 200
        else:
            return jsonify({
                "status": "failed",
                "statusCode": 500,
                "message": "Failed to create session.",
                "data": {}
            }), 500

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": f"Internal Server Error: {str(e)}",
            "data": {}
        }), 500
