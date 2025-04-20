import datetime
from decimal import Decimal
from flask_socketio import emit
import pymysql
from app.db import get_db

def register_menu_handlers(socketio):
    @socketio.on('get_menu_with_quantity')
    def handle_get_menu_with_quantity():
        try:
            db = get_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, name, price, description, image, menu_type_id
                FROM menu_items
                WHERE is_active = 1
                ORDER BY menu_type_id ASC;
            """)
            items = cursor.fetchall()
            for item in items:
                if isinstance(item['price'], Decimal):
                    item['price'] = float(item['price'])
            emit('menu_with_quantity_response', {
                'success': True,
                'data': items,
                'timestamp': datetime.datetime.now().isoformat()
            })
        except Exception as e:
            emit('menu_with_quantity_response', {
                'success': False,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            })
