from flask import Flask
from flask_cors import CORS
from flask import send_from_directory
from controllers.auth.login import login_controller
from controllers.auth.logout import logout_controller
from controllers.chat_session.chat import chat_controller
from controllers.chat_session.session import session_controller
from controllers.chat_session.language import language_controller

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Define the base URL for the API
BASE_URL = '/auth'

# default route
@app.route("/", methods=["GET"])
def index():
    return "Welcome to the Chat API!"

# login user
@app.route(BASE_URL+ "/login", methods=["POST"])
def login():
    return login_controller()

# logout user
@app.route(BASE_URL+ "/logout", methods=["POST"])
def logout():
    return logout_controller()

# Get languages
@app.route("/get_language", methods=["GET"])
def get_language():
    return language_controller()

# Create a session
@app.route("/session", methods=["POST"])
def session():
    return session_controller()

# Chat with mistral 
@app.route('/chat', methods=['POST'])
def chat():
    return chat_controller()

# Serve audio files to download
@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

# Serve lipsync JSON files to download
@app.route('/lipsync/<filename>')
def serve_lipsync(filename):
    return send_from_directory('static/lipsync', filename)

# app entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=3029)



