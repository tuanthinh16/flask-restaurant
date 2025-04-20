from flask import request
from flask_socketio import emit
import pymysql
from app.db import get_db

locked_tables = {}

def register_table_handlers(socketio):
    @socketio.on('get_tables')
    def handle_get_tables():
        try:
            db = get_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id, table_number, capacity, is_active,location FROM tables WHERE is_active = 1")
            rows = cursor.fetchall()
            cursor.close()
            db.close()

            tables_data = []
            for row in rows:
                status = 'locked' if row['id'] in locked_tables else 'available'
                tables_data.append({
                    'id': row['id'],
                    'table_number': row['table_number'],
                    'capacity': row['capacity'],
                    'location':row['location'],
                    'status': status
                })

            print(f"[get_tables] Gửi danh sách bàn: {tables_data}")
            emit('tables_data', tables_data)

        except Exception as e:
            print(f"[get_tables] Lỗi: {str(e)}")
            emit('table_error', {'error': 'Không thể lấy danh sách bàn'})

    @socketio.on('lock_table')
    def handle_lock_table(data):
        try:
            table_id = data.get('table_id')
            sid = request.sid
            print(f"[lock_table] Yêu cầu khoá bàn {table_id} từ SID: {sid}")

            if not table_id:
                emit('table_error', {'error': 'Thiếu table_id'})
                return

            if table_id in locked_tables:
                print(f"[lock_table] Bàn {table_id} đã bị khoá bởi {locked_tables[table_id]}")
                emit('table_error', {'error': 'Bàn đã bị khoá bởi người khác'})
            else:
                locked_tables[table_id] = sid
                print(f"[lock_table] Bàn {table_id} đã được khoá bởi {sid}")
                emit('table_locked', {'table_id': table_id}, broadcast=True)

        except Exception as e:
            print(f"[lock_table] Lỗi: {str(e)}")
            emit('table_error', {'error': 'Không thể khoá bàn'})

    @socketio.on('unlock_table')
    def handle_unlock_table(data):
        try:
            table_id = data.get('table_id')
            sid = request.sid
            print(f"[unlock_table] Yêu cầu mở khoá bàn {table_id} từ SID: {sid}")

            if locked_tables.get(table_id) == sid:
                locked_tables.pop(table_id, None)
                print(f"[unlock_table] Bàn {table_id} đã được mở khoá bởi {sid}")
                emit('table_unlocked', {'table_id': table_id}, broadcast=True)
            else:
                print(f"[unlock_table] Không có quyền mở khoá bàn {table_id}")
                emit('table_error', {'error': 'Bạn không có quyền mở khoá bàn này'})

        except Exception as e:
            print(f"[unlock_table] Lỗi: {str(e)}")
            emit('table_error', {'error': 'Không thể mở khoá bàn'})

    @socketio.on('disconnect')
    def handle_table_disconnect():
        sid = request.sid
        print(f"[disconnect] SID: {sid} ngắt kết nối, kiểm tra bàn đang khoá...")
        try:
            to_unlock = [tid for tid, s in locked_tables.items() if s == sid]
            for tid in to_unlock:
                locked_tables.pop(tid, None)
                print(f"[disconnect] Tự động mở khoá bàn {tid} do mất kết nối")
                emit('table_unlocked', {'table_id': tid}, broadcast=True)
        except Exception as e:
            print(f"[disconnect] Lỗi khi xử lý unlock: {str(e)}")
