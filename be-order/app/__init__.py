from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    socketio.init_app(app)
    return app
