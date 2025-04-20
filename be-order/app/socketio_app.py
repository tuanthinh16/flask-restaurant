from app import create_app, socketio
from app.handlers.menu import register_menu_handlers
from app.handlers.order import register_order_handlers
from app.handlers.disconnect import register_disconnect_handler
from app.handlers.auth import register_auth_handler
from app.handlers.tables import register_table_handlers
app = create_app()

register_menu_handlers(socketio)
register_order_handlers(socketio)
register_disconnect_handler(socketio)
register_table_handlers(socketio)
register_auth_handler(socketio)