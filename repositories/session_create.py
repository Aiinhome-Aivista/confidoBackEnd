from database.db_handler import get_db_connection

# call the stored procedure to create a session
def create_session_model(session_id, user_id, username, language_id, avatar_id, avatar_name):
    """
    Calls the 'session_create' stored procedure to insert session details.
    Does not return p_action (SP OUT param). Returns True if insert successful.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Call stored procedure (6 IN params + 1 OUT param)
        cursor.callproc("session_create", [
            session_id,
            user_id,
            username,
            language_id,
            avatar_id,
            avatar_name,
            ""  # OUT param placeholder
        ])

        conn.commit()
        cursor.close()
        conn.close()

        return True  # Success

    except Exception as e:
        raise Exception(f"Database error: {str(e)}")
