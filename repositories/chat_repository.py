from database.db_handler import get_db_connection
import json

# Function to check if a session exists
def get_language_by_session(session_id):
    """
    Uses sp_get_session_info → returns dict with user_id & language_name
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc("get_session_language", (session_id,))
        for res in cursor.stored_results():
            row = res.fetchone()
            return row  # {'user_id': ..., 'language_name': ...}
    finally:
        conn.close()

# Function to save communication history in database
def save_communication_history(session_id, history, language_name, user_id):
    """
    Calls sp_insert_communication to save final chat history
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.callproc("insert_communication", (
            session_id,
            user_id,
            json.dumps(history),
            language_name
        ))
        conn.commit()
    finally:
        conn.close()
