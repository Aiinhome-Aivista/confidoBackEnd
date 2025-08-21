from database.db_handler import get_db_connection

# Handle user logout through stored procedure
def logout_user_model(email, is_logged_in):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Call stored procedure (2 IN params + OUT param as session var)
        cursor.execute(
            "CALL user_logout(%s, %s, @p_action)",
            (email, is_logged_in)
        )

        # Retrieve OUT parameter value
        cursor.execute("SELECT @p_action AS action")
        result = cursor.fetchone()

        conn.commit()
        cursor.close()
        conn.close()

        return result["action"] if result else None

    except Exception as e:
        raise Exception(f"Database error: {str(e)}")
