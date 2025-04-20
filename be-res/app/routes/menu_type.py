import datetime
from flask import Blueprint, request, jsonify, make_response, current_app
from app.db import get_connection
from utils.dateTimeConvert import datetime_to_number
from utils.tokenRequired import token_required
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

menu_type_bp = Blueprint('menu_type', __name__)
CORS(menu_type_bp, origins="*")

@menu_type_bp.route('/', methods=['GET'])
def get_all_menu_types():
    try:
        current_app.logger.info("Fetching all active menu types")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, menu_type_name FROM menu_type WHERE is_active = 1")
        rows = cursor.fetchall()
        conn.close()
        result = [{'id': r[0], 'menu_type_name': r[1]} for r in rows]
        return make_response(jsonify(result), 200)
    except Exception as e:
        current_app.logger.error(f"Error fetching all menu types: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@menu_type_bp.route('/<int:id>', methods=['GET'])
def get_menu_type_by_id(id):
    try:
        current_app.logger.info(f"Fetching menu type with id: {id}")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, menu_type_name FROM menu_type WHERE id = %s AND is_active = 1", (id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return make_response(jsonify({'id': row[0], 'menu_type_name': row[1]}), 200)
        current_app.logger.warning(f"Menu type with id {id} not found")
        return make_response(jsonify({'message': 'Menu type not found'}), 404)
    except Exception as e:
        current_app.logger.error(f"Error fetching menu type with id {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@menu_type_bp.route('/', methods=['POST'])
@token_required
def create_menu_type(user_info):
    try:
        data = request.get_json()
        name = data.get('menu_type_name')
        if not name:
            raise BadRequest("Missing 'menu_type_name'")
        create_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO menu_type (menu_type_name, creator, create_time, is_active) VALUES (%s, %s, %s, 1)",
            (name, 'admin', create_time)
        )
        conn.commit()
        conn.close()
        current_app.logger.info(f"Created menu type: {name}")
        return make_response(jsonify({'message': 'Menu type created'}), 201)
    except Exception as e:
        current_app.logger.error(f"Error creating menu type: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@menu_type_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_menu_type(id, user_info):
    try:
        data = request.get_json()
        name = data.get('menu_type_name')
        if not name:
            raise BadRequest("Missing 'menu_type_name'")
        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE menu_type SET menu_type_name = %s, modifier = 'admin', modify_time = %s WHERE id = %s AND is_active = 1",
            (name, modify_time, id)
        )
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.warning(f"Menu type with id {id} not found or not active")
            return make_response(jsonify({'message': 'Menu type not found or not active'}), 404)
        current_app.logger.info(f"Updated menu type with id: {id}")
        return make_response(jsonify({'message': 'Menu type updated'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error updating menu type with id {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@menu_type_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_menu_type(id, user_info):
    try:
        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE menu_type SET is_active = 0, modifier = 'admin', modify_time = %s WHERE id = %s AND is_active = 1",
            (modify_time, id)
        )
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.warning(f"Menu type with id {id} not found or already inactive")
            return make_response(jsonify({'message': 'Menu type not found or already inactive'}), 404)
        current_app.logger.info(f"Deleted (deactivated) menu type with id: {id}")
        return make_response(jsonify({'message': 'Menu type deleted'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error deleting menu type with id {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)
