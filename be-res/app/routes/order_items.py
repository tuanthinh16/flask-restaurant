from flask import Blueprint, request, jsonify, make_response
from app.db import get_connection
from utils.dateTimeConvert import datetime_to_number
import datetime
from utils.tokenRequired import is_admin, is_staff, token_required
from flask import current_app

order_items_bp = Blueprint('order_items', __name__)

@order_items_bp.route('/', methods=['GET'])
@token_required
def get_all_order_items(user_info):
    try:
        if not is_admin(user_info) or not is_staff(user_info):
            current_app.logger.warning(f"Permission denied for user {user_info['username']}")
            return make_response(jsonify({'message': 'Permission denied'}), 403)
        
        item_id = request.args.get('id', type=int)
        start = request.args.get('start', type=int)
        limit = request.args.get('limit', type=int)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if item_id:
            current_app.logger.info(f"Fetching order item with id: {item_id}")
            cursor.execute("SELECT * FROM order_items WHERE id = %s AND is_active = 1", (item_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                current_app.logger.warning(f"Order item {item_id} not found.")
                return make_response(jsonify({'message': 'Order item not found'}), 404)
            return jsonify(row)

        sql = "SELECT * FROM order_items WHERE is_active = 1 ORDER BY id DESC"
        params = []
        if limit is not None and start is not None:
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, start])

        current_app.logger.info(f"Fetching order items with limit={limit}, start={start}")
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        current_app.logger.error(f"Error fetching order items: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@order_items_bp.route('/', methods=['POST'])
@token_required
def add_order_item(user_info):
    try:
        if not is_admin(user_info) or not is_staff(user_info):
            current_app.logger.warning(f"Permission denied for user {user_info['username']}")
            return make_response(jsonify({'message': 'Permission denied'}), 403)

        data = request.get_json()
        now = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO order_items (
                creator, create_time, is_active,
                order_id, menu_item_id, quantity, price
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            user_info['username'],
            now,
            1,  # Active by default
            data['order_id'],
            data['menu_item_id'],
            data['quantity'],
            data['price']
        ))
        conn.commit()
        conn.close()

        current_app.logger.info(f"Order item added successfully by user {user_info['username']}")
        return make_response(jsonify({'message': 'Order item added successfully'}), 201)
    except Exception as e:
        current_app.logger.error(f"Error adding order item: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@order_items_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_order_item(id, user_info):
    try:
        if not is_admin(user_info) or not is_staff(user_info):
            current_app.logger.warning(f"Permission denied for user {user_info['username']}")
            return make_response(jsonify({'message': 'Permission denied'}), 403)
        
        data = request.get_json()
        now = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE order_items SET
                modifier = %s,
                modify_time = %s,
                order_id = %s,
                menu_item_id = %s,
                quantity = %s,
                price = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (
            user_info['username'],
            now,
            data['order_id'],
            data['menu_item_id'],
            data['quantity'],
            data['price'],
            id
        ))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Order item {id} not found or already inactive.")
            return make_response(jsonify({'message': 'Order item not found'}), 404)

        current_app.logger.info(f"Order item {id} updated successfully by user {user_info['username']}")
        return make_response(jsonify({'message': 'Order item updated successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error updating order item {id}: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@order_items_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_order_item(id, user_info):
    try:
        if not is_admin(user_info):
            current_app.logger.warning(f"Permission denied for user {user_info['username']}")
            return make_response(jsonify({'message': 'Permission denied'}), 403)

        current_app.logger.info(f"Deleting order item {id} by user {user_info['username']}")
        now = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE order_items SET
                is_active = 0,
                modifier = %s,
                modify_time = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (user_info['username'], now, id))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Order item {id} not found or already inactive.")
            return make_response(jsonify({'message': 'Order item not found'}), 404)

        current_app.logger.info(f"Order item {id} deleted successfully by user {user_info['username']}")
        return make_response(jsonify({'message': 'Order item deleted successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error deleting order item {id}: {e}")
        return make_response(jsonify({'error': str(e)}), 500)
