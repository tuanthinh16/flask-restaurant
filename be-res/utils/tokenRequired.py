from flask import jsonify, request
from functools import wraps


from utils.decodeToken import decode_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        decoded = decode_token(token)
        if decoded.get('expired'):
            return jsonify({'message': decoded['error']}), 401

        # Gắn user info vào kwargs nếu cần
        kwargs['user_info'] = decoded
        return f(*args, **kwargs)
    return decorated
def is_admin(user_info):
    return user_info.get('role') == 'admin'
def is_user(user_info):
    return user_info.get('role') == 'user'
def is_staff(user_info):
    return user_info.get('role') == 'staff'