from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request
import logging

from utils.cacheDB import init_db
from .routes.menu import menu_bp
from .routes.menu_type import menu_type_bp
from .routes.user import users_bp
from .login import login_bp
from .routes.table import tables_bp
from .routes.inventory import inventory_bp
from .routes.order import orders_bp
from .routes.inventory_log import inventory_logs_bp
from .routes.admin import admin_bp
from .routes.reservations import reservations_bp
from .routes.translate import translate_bp
from .routes.image import img_bp
from flask_cors import CORS
from .extensions import limiter,cache
import pytz

class TZFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, tz=None):
        super().__init__(fmt, datefmt)
        self.tz = tz or pytz.utc

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, self.tz)
        return dt.strftime(datefmt or self.default_time_format)

def create_app():
    app = Flask(__name__)
    # Configure CORS before other extensions
    CORS(app, 
        resources={
            r"/*": {
                "origins": "*", 
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
        })
    
    # Disable strict slashes to prevent redirects
    app.url_map.strict_slashes = False
    limiter.init_app(app)  # ✅ Khởi tạo limiter

    cache.init_app(app)  # ✅ Khởi tạo cache
    # Thiết lập logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Thiết lập mức độ log

    # Cấu hình ghi log vào file với RotatingFileHandler
    log_file_handler = RotatingFileHandler('LogSystem.log', maxBytes=10*1024*1024, backupCount=3)  # Max 10MB và lưu tối đa 3 file backup
    log_file_handler.setLevel(logging.INFO)  # Mức độ log cho file (INFO và cao hơn)
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    formatter = TZFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', tz=vn_tz)
    log_file_handler.setFormatter(formatter)
    
    app.debug = False
    # Thêm handler vào logger của app
    if not app.debug:
        app.logger.addHandler(log_file_handler)

    # Optionally, you can set the logger for `current_app` as well:
    app.logger.setLevel(logging.DEBUG)
    init_db()
    # Register the logger into the app context (Optional but useful for consistency)
    app.logger = logger
    @app.before_request
    def before_request_func():
        method = request.method  # GET, POST, PUT, DELETE
        path = request.path      # Đường dẫn URL
        app.logger.info(f"[{method}] {path}")
    # routes
    app.register_blueprint(menu_bp, url_prefix='/api/menu',limiter=limiter)
    app.register_blueprint(menu_type_bp, url_prefix='/api/menu-type')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(tables_bp, url_prefix='/api/tables')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(inventory_logs_bp, url_prefix='/api/inventory-logs')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(reservations_bp, url_prefix='/api/reservations')
    app.register_blueprint(translate_bp, url_prefix='/api/translate')
    app.register_blueprint(img_bp,url_prefix='/api/image')
    # Login
    app.register_blueprint(login_bp, url_prefix='/login')
    return app
