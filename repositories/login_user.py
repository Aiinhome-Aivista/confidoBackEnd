from database.db_handler import get_db_connection

def login_by_user_model(username, email, account_type, login_type, is_logged_in):
    """
    Calls the `user_login` stored procedure using mysql-connector.
    Returns the OUT parameter result along with user_id.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Call the stored procedure with 5 IN params + 2 OUT params
        cursor.execute(
            "CALL user_login(%s, %s, %s, %s, %s, @p_action, @p_user_id)",
            (username, email, account_type, login_type, is_logged_in)
        )

        # Fetch OUT parameters
        cursor.execute("SELECT @p_action AS action, @p_user_id AS user_id")
        result = cursor.fetchone()

        conn.commit()
        return result if result else None

    except Exception as e:
        raise Exception(f"Database error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
