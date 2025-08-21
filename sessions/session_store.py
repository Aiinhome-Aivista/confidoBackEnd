import json
import os

# Session store for chat history
STORE_FILE = "evaluated_chats.json"

# Load the store from the file
def _load_store():
    if not os.path.exists(STORE_FILE):
        return {}
    try:
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

# Save the store to the file
def _save_store(data):
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Function to save chat history in evaluated_chats.json
def save_chat_history(session_id, history):
    """
    Save the full chat history for a given session_id into evaluated_chats.json
    history: list of messages like [{"role": "user", "message": "Hi"}, {"role": "ai", "message": "Hello"}]
    """
    store = _load_store()
    formatted_history = []

    # Convert history into a single string with System/User/Ai labels
    chat_str = []
    for msg in history:
        role = msg.get("role", "system").capitalize()
        message = msg.get("message", "")
        chat_str.append(f"{role}: {message}")
    formatted_history.append({"chat_history": " ".join(chat_str)})

    if session_id not in store:
        store[session_id] = []

    store[session_id].append(formatted_history[0])
    _save_store(store)

# Function to get chat history for a session_id
def get_chat_history(session_id):
    """Return saved chat history for a session_id"""
    store = _load_store()
    return store.get(session_id, [])
