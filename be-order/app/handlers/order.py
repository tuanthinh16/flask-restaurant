import datetime
import time
from flask import request, session
from flask_socketio import emit, disconnect
from app.db import get_db

active_orders = {}

def register_order_handlers(socketio):
    @socketio.on('join_table')
    def handle_join_table(table_id):
        if table_id in active_orders:
            emit('order_error', {'error': 'Bàn đang được sử dụng'})
            disconnect()
        else:
            active_orders[table_id] = request.sid
            emit('order_joined', {'table_id': table_id})

    @socketio.on('order_update')
    def handle_order_update(data):
        table_id = data['tableId']
        order = data['order']
        emit('order_update', {
            'tableId': table_id,
            'order': order
        }, broadcast=True)

    @socketio.on('submit_order')
    def handle_submit_order(data):
        try:
            print(f"[submit_order] Received data: {data}")
            table_id = data['table_id']
            items = data['items']
            username = session.get('username')
            print(f"[submit_order] Username: {username}, SID: {request.sid}")

            if not username or username is None:
                emit('order_submission_result', {'success': False, 'error': 'Unauthenticated'})
                return

            if active_orders.get(table_id) != request.sid:
                print(f"[submit_order] SID mismatch: {active_orders.get(table_id)} != {request.sid}")
                emit('order_error', {'error': 'Không được phép xác nhận đơn này'})
                return

            db = get_db()
            cursor = db.cursor()

            timestamp = int(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
            total = 0
            detailed_items = []

            for item_id, qty in items.items():
                cursor.execute("SELECT price FROM menu_items WHERE id = %s", (item_id,))
                result = cursor.fetchone()
                if not result:
                    print(f"[submit_order] Item ID {item_id} not found.")
                    continue
                price = float(result[0])
                total += price * qty
                detailed_items.append((item_id, qty, price))
                print(f"[submit_order] Item {item_id} x{qty} @ {price} => {price * qty}")

            print(f"[submit_order] Total: {total}, Items: {detailed_items}")

            cursor.execute("""
                INSERT INTO orders (creator, create_time, table_id, order_time, total, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, timestamp, table_id, timestamp, total, "pending"))
            order_id = cursor.lastrowid
            print(f"[submit_order] Created order ID: {order_id}")

            for item_id, qty, price in detailed_items:
                cursor.execute("""
                    INSERT INTO order_items (creator, create_time, order_id, menu_item_id, quantity, price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, timestamp, order_id, item_id, qty, price))

            db.commit()
            cursor.close()
            db.close()

            active_orders.pop(table_id, None)
            print(f"[submit_order] Order submission successful for table {table_id}")
            emit('order_submission_result', {'success': True, 'order_id': order_id})
        except Exception as e:
            print(f"[submit_order] Error: {str(e)}")
            emit('order_submission_result', {'success': False, 'error': str(e)})

    @socketio.on('disconnect')
    def handle_disconnect():
        for table_id, sid in list(active_orders.items()):
            if sid == request.sid:
                active_orders.pop(table_id)
