from flask import request
from flask_socketio import emit
import pymysql
from app.db import get_db

def register_table_handlers(socketio):
    @socketio.on('get_tables')
    def handle_get_tables():
        try:
            db = get_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT id, table_number, capacity, is_active, location, status FROM tables WHERE is_active = 1")
            rows = cursor.fetchall()
            cursor.close()
            db.close()

            tables_data = []
            for row in rows:
                status = 'locked' if row['status'] == 1 else 'available'
                tables_data.append({
                    'id': row['id'],
                    'table_number': row['table_number'],
                    'capacity': row['capacity'],
                    'location': row['location'],
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

            db = get_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT status FROM tables WHERE id = %s", (table_id,))
            row = cursor.fetchone()

            if not row:
                emit('table_error', {'error': 'Bàn không tồn tại'})
            elif row['status'] == 1:
                print(f"[lock_table] Bàn {table_id} đã bị khoá")
                emit('table_error', {'error': 'Bàn đã bị khoá bởi người khác'})
            else:
                cursor.execute("UPDATE tables SET status = 1 WHERE id = %s", (table_id,))
                db.commit()
                print(f"[lock_table] Bàn {table_id} đã được khoá")
                emit('table_locked', {'table_id': table_id}, broadcast=True)

            cursor.close()
            db.close()

        except Exception as e:
            print(f"[lock_table] Lỗi: {str(e)}")
            emit('table_error', {'error': 'Không thể khoá bàn'})

    @socketio.on('unlock_table')
    def handle_unlock_table(data):
        try:
            table_id = data.get('table_id')
            sid = request.sid
            print(f"[unlock_table] Yêu cầu mở khoá bàn {table_id} từ SID: {sid}")

            if not table_id:
                emit('table_error', {'error': 'Thiếu table_id'})
                return

            db = get_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT status FROM tables WHERE id = %s", (table_id,))
            row = cursor.fetchone()

            if not row:
                emit('table_error', {'error': 'Bàn không tồn tại'})
            elif row['status'] == 1:
                cursor.execute("UPDATE tables SET status = 0 WHERE id = %s", (table_id,))
                db.commit()
                print(f"[unlock_table] Bàn {table_id} đã được mở khoá")
                emit('table_unlocked', {'table_id': table_id}, broadcast=True)
            else:
                print(f"[unlock_table] Bàn {table_id} không bị khoá")
                emit('table_error', {'error': 'Bàn không bị khoá hoặc đã được mở'})

            cursor.close()
            db.close()

        except Exception as e:
            print(f"[unlock_table] Lỗi: {str(e)}")
            emit('table_error', {'error': 'Không thể mở khoá bàn'})
