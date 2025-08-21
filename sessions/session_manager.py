import time

# Session management for chat sessions
sessions = {}

# Function to start a new session
def start_session(session_id, duration_minutes):
    sessions[session_id] = {
        "start_time": time.time(),
        "duration": duration_minutes * 60,
        "history": [],
        "active": True
    }

# Function to check if a session is active
def is_session_active(session_id):
    session = sessions.get(session_id)
    if not session:
        return False
    elapsed = time.time() - session["start_time"]
    if elapsed > session["duration"]:
        session["active"] = False
        return False
    return session["active"]

# Function to add a message to the session history
def add_message(session_id, role, message):
    if session_id in sessions:
        sessions[session_id]["history"].append({"role": role, "message": message})

# Function to get the session history
def get_history(session_id):
    return sessions.get(session_id, {}).get("history", [])

# Function to check if a session exists
def session_exists(session_id):
    return session_id in sessions
