from flask import jsonify
from mysql.connector import connect, Error
from config import MYSQL_CONFIG

# get language controller
def language_controller():
    try:
        conn = connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Fetch all active languages from table
        cursor.execute("SELECT language_id, language_name FROM language_master")
        languages = cursor.fetchall()
        # print(f"Fetched languages: {languages}")

        if languages:
            return jsonify(
                {
                    "status": True,
                    "status_code": 200,
                    "message": "Language fetched successfully",
                    "data": languages,
                }
            )
        else:
            return jsonify(
                {
                    "status": False,
                    "status_code": 404,
                    "message": "No languages found",
                    "data": [],
                }
            )

    except Error as e:
        return jsonify(
            {
                "status": False,
                "status_code": 500,
                "message": f"Database error: {str(e)}",
                "data": [],
            }
        )

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass