import jwt
from flask import request, jsonify
from functools import wraps

from utils.config import SECRET_KEY


def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return {
            'username': payload.get('username'),
            'role': payload.get('role'),
            'expired': False
        }
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired', 'expired': True}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token', 'expired': True}
