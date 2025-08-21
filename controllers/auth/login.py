from flask import request, jsonify
from repositories.login_user import login_by_user_model

VALID_LOGIN_TYPES = ["google", "facebook"]
VALID_IS_LOGGEDIN = ["true", "false"]

def login_controller():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": "Request body is missing or invalid JSON"
            }), 400

        username = data.get("name")
        email = data.get("email")
        login_type = data.get("loginType")
        account_type = data.get("accountType", "free").lower()
        is_logged_in = data.get("isLoggedIn", "true").lower()

        # Check required fields
        missing_fields = [f for f in ["name", "email", "loginType"] if not data.get(f)]
        if missing_fields:
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": f"Missing required field(s): {', '.join(missing_fields)}"
            }), 400

        # Validate values
        if login_type.lower() not in VALID_LOGIN_TYPES:
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": f"Invalid loginType. Must be one of {VALID_LOGIN_TYPES}"
            }), 400

        if is_logged_in not in VALID_IS_LOGGEDIN:
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": f"Invalid isLoggedIn value. Must be one of {VALID_IS_LOGGEDIN}"
            }), 400

        # Call stored procedure
        result = login_by_user_model(username, email, account_type, login_type.lower(), is_logged_in)
        action_message = result["action"] if result else None
        user_id = result["user_id"] if result else None
        
        print(f"Login action: {action_message}, User ID: {user_id} and Email: {email}")

        # Set status code
        if action_message in ["User Login Successful.", "User Already Logged In.", "User Updated and Logged In Successfully."]:
            status_code = 200
        elif action_message == "User Added Successfully.":
            status_code = 201
        else:
            status_code = 500

        return jsonify({
            "status": True if status_code in (200, 201) else False,
            "statusCode": status_code,
            "message": action_message or "Unknown error",
            "data": {
                "name": username,
                "email": email,
                "user_id": user_id
            } if status_code in (200, 201) else {}
        }), status_code

    except Exception as e:
        return jsonify({
            "status": False,
            "statusCode": 500,
            "message": f"Internal Server Error: {str(e)}"
        }), 500
