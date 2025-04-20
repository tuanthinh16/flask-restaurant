import datetime
from flask import Blueprint, request, jsonify, make_response, current_app
from utils.translateDict import translate_dict
from utils.dateTimeConvert import datetime_to_number
from app.db import get_connection
from utils.tokenRequired import token_required

inventory_bp = Blueprint('inventory', __name__)

# GET all or by id
@inventory_bp.route('/', methods=['GET'])
@token_required
def get_inventory(user_info):
    try:
        item_id = request.args.get('id')
        limit = request.args.get('limit', type=int)
        start = request.args.get('start', type=int)
        target_lang = request.args.get('target_lang')  # Ngôn ngữ đích nếu có
        conn = get_connection()
        cursor = conn.cursor()
        if item_id:
            cursor.execute("SELECT id, item_name, quantity, unit, threshold FROM inventory WHERE id = %s AND is_active = 1", (item_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                current_app.logger.info(f"Fetched inventory item with ID {item_id}.")
                return make_response(jsonify({
                    'id': row[0],
                    'item_name': row[1],
                    'quantity': row[2],
                    'unit': row[3],
                    'threshold': row[4]
                }), 200)
            if target_lang:
                result = translate_dict(result, source_lang="en", target_lang=target_lang)
            current_app.logger.warning(f"Item with ID {item_id} not found.")
            return make_response(jsonify({'message': 'Item not found'}), 404)
        else:
            base_sql = """SELECT id, item_name, quantity, unit, threshold FROM inventory WHERE is_active = 1"""
            params = []
            if limit is not None and start is not None:
                base_sql += " LIMIT %s OFFSET %s"
                params.extend([limit, start])
            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
            conn.close()
            result = [{
                'id': row[0],
                'item_name': row[1],
                'quantity': row[2],
                'unit': row[3],
                'threshold': row[4]
            } for row in rows]
            if target_lang:
                result = [translate_dict(item, source_lang="en", target_lang=target_lang) for item in result]
            current_app.logger.info(f"Fetched inventory items with limit {limit} and start {start}.")
            return make_response(jsonify(result), 200)
    except Exception as e:
        current_app.logger.error(f"Error while fetching inventory items: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)


# POST create
@inventory_bp.route('/', methods=['POST'])
@token_required
def add_inventory(user_info):
    try:
        data = request.get_json()
        create_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO inventory (item_name, quantity, unit, threshold, creator, create_time, is_active)
                 VALUES (%s, %s, %s, %s, %s, %s, 1)"""
        cursor.execute(sql, (
            data['item_name'], data['quantity'], data['unit'],
            data['threshold'], user_info['username'], create_time
        ))
        conn.commit()
        conn.close()
        current_app.logger.info(f"Inventory item '{data['item_name']}' added by {user_info['username']}.")
        return make_response(jsonify({'message': 'Inventory item added'}), 201)
    except Exception as e:
        current_app.logger.error(f"Error while adding inventory item: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)


# PUT update
@inventory_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_inventory(id, user_info):
    try:
        data = request.get_json()
        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """UPDATE inventory
                 SET item_name = %s, quantity = %s, unit = %s, threshold = %s,
                     modifier = %s, modify_time = %s
                 WHERE id = %s AND is_active = 1"""
        cursor.execute(sql, (
            data['item_name'], data['quantity'], data['unit'],
            data['threshold'], user_info['username'], modify_time, id
        ))
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.warning(f"Item with ID {id} not found.")
            return make_response(jsonify({'message': 'Item not found'}), 404)
        current_app.logger.info(f"Inventory item with ID {id} updated by {user_info['username']}.")
        return make_response(jsonify({'message': 'Inventory item updated'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error while updating inventory item with ID {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)


# DELETE (soft delete)
@inventory_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_inventory(id, user_info):
    try:
        if user_info['role'] != 'admin':
            current_app.logger.warning(f"Permission denied for user {user_info['username']} to delete inventory item with ID {id}.")
            return make_response(jsonify({'message': 'Permission denied'}), 403)
        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """UPDATE inventory
                 SET is_active = 0, modifier = %s, modify_time = %s
                 WHERE id = %s AND is_active = 1"""
        cursor.execute(sql, (user_info['username'], modify_time, id))
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.warning(f"Item with ID {id} not found or already deleted.")
            return make_response(jsonify({'message': 'Item not found or already deleted'}), 404)
        current_app.logger.info(f"Inventory item with ID {id} deleted by {user_info['username']}.")
        return make_response(jsonify({'message': 'Inventory item deleted'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error while deleting inventory item with ID {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)
