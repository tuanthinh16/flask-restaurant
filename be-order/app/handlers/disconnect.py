from flask import request
from app.handlers.order import active_orders
from flask_socketio import SocketIO

def register_disconnect_handler(socketio: SocketIO):
    @socketio.on('disconnect')
    def on_disconnect():
        for table_id, sid in list(active_orders.items()):
            if sid == request.sid:
                active_orders.pop(table_id)
