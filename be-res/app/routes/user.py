import datetime
from flask import Blueprint, request, jsonify, make_response, current_app
from app.db import get_connection
from utils.dateTimeConvert import datetime_to_number
from flask_cors import CORS
from utils.hashPassword import hash_password
from utils.tokenRequired import token_required

users_bp = Blueprint('users', __name__)
CORS(users_bp, origins="*")

@users_bp.route('/', methods=['GET'])
@token_required
def get_users(user_info):
    try:
        if user_info['role'] != 'admin':
            current_app.logger.warning(f"Permission denied for user {user_info['username']} - Not an admin")
            return make_response(jsonify({'message': 'Permission denied'}), 403)

        user_id = request.args.get('id', type=int)
        start = request.args.get('start', type=int)
        limit = request.args.get('limit', type=int)

        conn = get_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""SELECT id, username, full_name, email, phone, role, last_login 
                              FROM users WHERE id = %s AND is_active = 1""", (user_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return make_response(jsonify({
                    'id': row[0],
                    'username': row[1],
                    'full_name': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'role': row[5],
                    'last_login': row[6]
                }), 200)
            else:
                current_app.logger.info(f"User with id {user_id} not found.")
                return make_response(jsonify({'message': 'User not found'}), 404)
        else:
            sql = """SELECT id, username, full_name, email, phone, role, last_login 
                     FROM users WHERE is_active = 1"""
            params = []

            if limit is not None and start is not None:
                sql += " LIMIT %s OFFSET %s"
                params.extend([limit, start])

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            result = [{
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'email': row[3],
                'phone': row[4],
                'role': row[5],
                'last_login': row[6]
            } for row in rows]
            current_app.logger.info(f"Fetched {len(result)} users.")
            return make_response(jsonify(result), 200)
    except Exception as e:
        current_app.logger.error(f"Error fetching users: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@users_bp.route('/', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        current_app.logger.info(f"Creating user: {data}")
        create_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO users (creator, create_time, is_active, role, last_login, username, password, full_name, email, phone)
            VALUES ('admin', %s, 1, %s, 0, %s, %s, %s, %s, %s)
        """
        cursor.execute("SELECT id FROM users WHERE username = %s AND is_active = 1", (data['username'],))
        if cursor.fetchone():
            current_app.logger.warning(f"Username {data['username']} already exists.")
            return make_response(jsonify({'message': 'Username already exists'}), 400)

        cursor.execute(sql, (
            create_time,
            data['role'],
            data['username'],
            hash_password(data['password']),  # hash trước khi gửi lên hoặc hash tại đây nếu cần
            data['full_name'],
            data['email'],
            data['phone']
        ))
        conn.commit()
        conn.close()
        current_app.logger.info(f"User {data['username']} created successfully.")
        return make_response(jsonify({'message': 'User created successfully'}), 201)
    except Exception as e:
        current_app.logger.error(f"Error creating user: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@users_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_user(id, user_info):
    try:
        if user_info['role'] != 'admin' or user_info['id'] != id:
            current_app.logger.warning(f"Permission denied for user {user_info['username']} - Not authorized to update user {id}")
            return make_response(jsonify({'message': 'Permission denied'}), 403)
        data = request.get_json()
        current_app.logger.info(f"Updating user {id} with data: {data}")
        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE users SET full_name = %s, email = %s, phone = %s, role = %s, modifier = 'admin', modify_time = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (
            data['full_name'],
            data['email'],
            data['phone'],
            data['role'],
            modify_time,
            id
        ))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.info(f"User with id {id} not found or not active.")
            return make_response(jsonify({'message': 'User not found or not active'}), 404)
        current_app.logger.info(f"User {id} updated successfully.")
        return make_response(jsonify({'message': 'User updated successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error updating user: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@users_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_user(id, user_info):
    try:
        if user_info['role'] != 'admin':
            current_app.logger.warning(f"Permission denied for user {user_info['username']} - Not an admin")
            return make_response(jsonify({'message': 'Permission denied'}), 403)
        current_app.logger.info(f"Deleting user {id}")
        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = "UPDATE users SET is_active = 0, modifier = %s, modify_time = %s WHERE id = %s AND is_active = 1"
        cursor.execute(sql, (user_info['username'], modify_time, id))
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.info(f"User with id {id} not found or already inactive.")
            return make_response(jsonify({'message': 'User not found or already inactive'}), 404)
        current_app.logger.info(f"User {id} deleted successfully.")
        return make_response(jsonify({'message': 'User deleted successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error deleting user: {e}")
        return make_response(jsonify({'error': str(e)}), 500)
