import os
from flask import request, session
import jwt

secret_key = os.getenv('JWT_SECRET_KEY','thinhvipnghean')
def register_auth_handler(socketio):
    @socketio.on('connect')
    def handle_connect(auth):  # thêm tham số auth
        token = auth.get('token') if auth else None
        print(f"token: {token}")
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            request.username = payload['username']
            session['username'] = payload['username']  # Lưu vào session của socket
        except Exception as e:
            print('Invalid token:', e)
            return False  # từ chối kết nối

