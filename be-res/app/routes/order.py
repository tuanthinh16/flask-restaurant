import datetime
from flask import Blueprint, request, jsonify, make_response, current_app
from utils.dateTimeConvert import datetime_to_number
from app.db import get_connection
from utils.tokenRequired import is_admin, is_staff, token_required

orders_bp = Blueprint('orders', __name__)

# GET all or by id
@orders_bp.route('/', methods=['GET'])
@token_required
def get_orders(user_info):
    try:
        current_app.logger.info(f"User {user_info['username']} is accessing order data")
        if not is_admin(user_info) or not is_staff(user_info):
            current_app.logger.warning(f"User {user_info['username']} does not have permission to access orders")
            return make_response(jsonify({'message': 'Permission denied'}), 403)

        order_id = request.args.get('id')
        limit = request.args.get('limit', type=int)
        start = request.args.get('start', type=int)

        current_app.logger.info(f"Requesting orders with parameters - order_id: {order_id}, limit: {limit}, start: {start}")

        conn = get_connection()
        cursor = conn.cursor()
        
        if order_id:
            cursor.execute("""SELECT id, table_id, order_time, status, total 
                              FROM orders WHERE id = %s AND is_active = 1""", (order_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                current_app.logger.info(f"Order found: {row}")
                return make_response(jsonify({
                    'id': row[0],
                    'table_id': row[1],
                    'order_time': row[2],
                    'status': row[3],
                    'total': row[4]
                }), 200)
            current_app.logger.warning(f"Order with id {order_id} not found")
            return make_response(jsonify({'message': 'Order not found'}), 404)
        else:
            base_sql = """SELECT id, table_id, order_time, status, total 
                          FROM orders WHERE is_active = 1"""
            params = []
            if limit is not None and start is not None:
                base_sql += " LIMIT %s OFFSET %s"
                params.extend([limit, start])
            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
            conn.close()
            result = [dict(id=row[0], table_id=row[1], order_time=row[2],
                           status=row[3], total=row[4]) for row in rows]
            current_app.logger.info(f"Returning {len(result)} orders")
            return make_response(jsonify(result), 200)
    except Exception as e:
        current_app.logger.error(f"Error while fetching orders: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

# POST create
@orders_bp.route('/', methods=['POST'])
@token_required
def add_order(user_info):
    try:
        current_app.logger.info(f"User {user_info['username']} is creating a new order")
        if not is_admin(user_info) or not is_staff(user_info):
            current_app.logger.warning(f"User {user_info['username']} does not have permission to create orders")
            return make_response(jsonify({'message': 'Permission denied'}), 403)
        
        data = request.get_json()
        now = datetime.datetime.now()
        create_time = datetime_to_number(now)
        order_time = datetime_to_number(now)

        conn = get_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO orders (table_id, order_time, status, total, creator, create_time, is_active)
                 VALUES (%s, %s, %s, %s, %s, %s, 1)"""
        cursor.execute(sql, (
            data['table_id'], order_time, data.get('status', 'pending'),
            data['total'], user_info['username'], create_time
        ))
        conn.commit()
        conn.close()
        current_app.logger.info(f"Order created successfully by {user_info['username']}")
        return make_response(jsonify({'message': 'Order created'}), 201)
    except Exception as e:
        current_app.logger.error(f"Error while creating order: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

# PUT update
@orders_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_order(id, user_info):
    try:
        current_app.logger.info(f"User {user_info['username']} is updating order with id {id}")
        if not is_admin(user_info) or not is_staff(user_info):
            current_app.logger.warning(f"User {user_info['username']} does not have permission to update orders")
            return make_response(jsonify({'message': 'Permission denied'}), 403)

        data = request.get_json()
        modify_time = datetime_to_number(datetime.datetime.now())

        conn = get_connection()
        cursor = conn.cursor()
        sql = """UPDATE orders
                 SET table_id = %s, status = %s, total = %s,
                     modifier = %s, modify_time = %s
                 WHERE id = %s AND is_active = 1"""
        cursor.execute(sql, (
            data['table_id'], data['status'], data['total'],
            user_info['username'], modify_time, id
        ))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Order with id {id} not found for update")
            return make_response(jsonify({'message': 'Order not found'}), 404)
        current_app.logger.info(f"Order with id {id} updated successfully")
        return make_response(jsonify({'message': 'Order updated'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error while updating order with id {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

# DELETE (soft delete)
@orders_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_order(id, user_info):
    try:
        current_app.logger.info(f"User {user_info['username']} is deleting order with id {id}")
        if not is_admin(user_info) or not is_staff(user_info):
            current_app.logger.warning(f"User {user_info['username']} does not have permission to delete orders")
            return make_response(jsonify({'message': 'Permission denied'}), 403)
        
        modify_time = datetime_to_number(datetime.datetime.now())

        conn = get_connection()
        cursor = conn.cursor()
        sql = """UPDATE orders
                 SET is_active = 0, modifier = %s, modify_time = %s
                 WHERE id = %s AND is_active = 1"""
        cursor.execute(sql, (user_info['username'], modify_time, id))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Order with id {id} not found or already deleted")
            return make_response(jsonify({'message': 'Order not found or already deleted'}), 404)
        current_app.logger.info(f"Order with id {id} deleted successfully")
        return make_response(jsonify({'message': 'Order deleted'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error while deleting order with id {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)
