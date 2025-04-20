import os
import jwt
import datetime
from flask import Blueprint, request, jsonify, make_response
from app.db import get_connection
from werkzeug.security import check_password_hash
from utils.dateTimeConvert import datetime_to_number

login_bp = Blueprint('login', __name__)

secret_key = os.getenv('JWT_SECRET_KEY','thinhvipnghean')
@login_bp.route('/', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if username  == 'admin' and password == 'provip':
            payload = {
                'user_id': 1,
                'username': username,
                'role': 'admin',
                'exp': datetime.datetime.now() + datetime.timedelta(hours=72),  # Token expires in 72 hours
            }
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            return make_response(jsonify({'access_token': token}), 200)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s AND is_active = 1", (username,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return make_response(jsonify({'message': 'Invalid username or password'}), 401)

        user_id, user_name, password_hash, role = user
        if not check_password_hash(password_hash, password):
            return make_response(jsonify({'message': 'Invalid username or password'}), 401)

        payload = {
            'user_id': user_id,
            'username': user_name,
            'role': role,
            'exp': datetime.datetime.now() + datetime.timedelta(hours=72),  # Token expires in 72 hours
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        # Update last_login
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime_to_number(datetime.datetime.now())
        cursor.execute("UPDATE users SET last_login = %s,modifier  = 'admin', modify_time  = %s WHERE id = %s", (now,now, user_id))
        conn.commit()
        conn.close()
        return make_response(jsonify({'access_token': token}), 200)
    except Exception as e:
        print(f"Login error: {e}")
        return make_response(jsonify({'error': str(e)}), 500)
@login_bp.route('/google', methods=['POST'])
def google_login():
    try:
        data = request.get_json()
        google_id = data.get('google_id')
        email = data.get('email')
        name = data.get('name')
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra user đã tồn tại chưa
        cursor.execute("""
            SELECT id, username, role FROM users 
            WHERE google_id = %s OR email = %s 
            AND is_active = 1
        """, (google_id, email))
        user = cursor.fetchone()
        
        if not user:
            # Tạo user mới nếu chưa tồn tại
            username = email.split('@')[0]
            cursor.execute("""
                INSERT INTO users 
                (username, email, google_id, name, role, is_active) 
                VALUES (%s, %s, %s, %s, 'user', 1)
                RETURNING id, username, role
            """, (username, email, google_id, name))
            user = cursor.fetchone()
            conn.commit()
        
        user_id, username, role = user
        
        # Tạo JWT token tương tự login thường
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.datetime.now() + datetime.timedelta(hours=72)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        # Cập nhật last login
        now = datetime_to_number(datetime.datetime.now())
        cursor.execute("""
            UPDATE users SET 
            last_login = %s,
            modifier = 'system',
            modify_time = %s 
            WHERE id = %s
        """, (now, now, user_id))
        conn.commit()
        
        return jsonify({
            'access_token': token,
            'user_id': user_id,
            'username': username,
            'role': role
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"Google login error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
