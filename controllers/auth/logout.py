from flask import request, jsonify
from repositories.logout_user import logout_user_model

# Allowed values for isLoggedIn
VALID_IS_LOGGEDIN = ["true", "false"]

# Logout Controller
def logout_controller():
    """
    Handles the logout request:
    - Validates JSON request body
    - Calls the logout model to update DB via stored procedure
    - Returns appropriate status and message
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": "Request body is missing or invalid JSON"
            }), 400

        # Extract fields from request body
        email = data.get("email")
        is_logged_in = data.get("isLoggedIn", "false").lower()  # default 'false'

        # Validate required fields
        if not email:
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": "Missing required field: email"
            }), 400

        # Validate isLoggedIn value
        if is_logged_in not in VALID_IS_LOGGEDIN:
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": f"Invalid isLoggedIn value. Must be one of {VALID_IS_LOGGEDIN}"
            }), 400

        # Call model → stored procedure
        action_message = logout_user_model(email, is_logged_in)

        # Determine status code based on action message
        if action_message in ["User has Logged Out Successfully", "User Already Logged Out"]:
            status_code = 200
        else:
            status_code = 500

        return jsonify({
            "status": True if status_code == 200 else False,
            "statusCode": status_code,
            "message": action_message or "Unknown error",
            "data": {
                "email": email
            } if status_code == 200 else {}
        }), status_code

    except Exception as e:
        return jsonify({
            "status": False,
            "statusCode": 500,
            "message": f"Internal Server Error: {str(e)}"
        }), 500
