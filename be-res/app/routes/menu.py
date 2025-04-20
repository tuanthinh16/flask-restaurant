import datetime
from flask import Blueprint, current_app, make_response, request, jsonify
from app.db import get_connection
from app.routes.admin import reset_cache
from utils.dateTimeConvert import datetime_to_number
from utils.tokenRequired import token_required
from app.extensions import cache, limiter
from utils.translateDict import translate_dict
menu_bp = Blueprint('menu', __name__)
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

CORS(menu_bp, origins="*")


@menu_bp.route('/', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
@limiter.limit("10 per minute")
def get_menu():
    try:
        # Lấy các tham số đầu vào
        item_id = request.args.get('id', type=int)
        start = request.args.get('start', type=int, default=0)
        limit = request.args.get('limit', type=int, default=10)
        target_lang = request.args.get('target_lang')  # lấy ngôn ngữ đích nếu có
        # Kiểm tra tính hợp lệ của limit và start
        if limit <= 0 or limit > 100:
            current_app.logger.warning(f"Invalid limit value: {limit}. Must be between 1 and 100.")
            raise BadRequest("Invalid limit value. Must be between 1 and 100.")
        if start < 0:
            current_app.logger.warning(f"Invalid start value: {start}. Must be greater than or equal to 0.")
            raise BadRequest("Invalid start value. Must be greater than or equal to 0.")

        # Kết nối cơ sở dữ liệu
        conn = get_connection()
        cursor = conn.cursor()
        # Lấy tổng số dòng
        cursor.execute("SELECT COUNT(*) FROM menu_items WHERE is_active = 1")
        total_rows = cursor.fetchone()[0]
        # Trường hợp tìm theo item_id
        if item_id:
            current_app.logger.info(f"Fetching menu item with id: {item_id}")
            cursor.execute("SELECT id, name, price, description,image,menu_type_id FROM menu_items WHERE id = %s AND is_active = 1", (item_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                result = {
                    'id': row[0],
                    'name': row[1],
                    'price': row[2],
                    'description': row[3],
                    'image_url': row[4],
                    'menu_type_id':row[5]
                }
                if target_lang:
                    current_app.logger.info(f"Translating result to {target_lang}")
                    result = translate_dict(result, source_lang="en", target_lang=target_lang)
                return make_response(jsonify({'total_rows': total_rows, 'data': result}), 200)
            else:
                current_app.logger.warning(f"Item with id {item_id} not found.")
                return make_response(jsonify({'message': 'Item not found'}), 404)
        else:
            # Truy vấn không có item_id, lấy danh sách menu
            sql = "SELECT id, name, price, description, image,menu_type_id FROM menu_items WHERE is_active = 1"
            params = []
            
            # Thêm LIMIT và OFFSET nếu có
            if limit is not None and start is not None:
                sql += " LIMIT %s OFFSET %s"
                params.extend([limit, start])

            current_app.logger.info(f"Fetching menu items with limit={limit}, start={start}")
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()

            result = [{
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'description': row[3],
                'image_url': row[4],
                'menu_type_id':row[5]

            } for row in rows]
            if target_lang:
                current_app.logger.info(f"Translating menu items to {target_lang}")
                result = [translate_dict(item, source_lang="en", target_lang=target_lang) for item in result]
            return make_response(jsonify({'total_rows': total_rows, 'data': result}), 200)

    except BadRequest as e:
        current_app.logger.error(f"Bad request: {e}")
        return make_response(jsonify({'error': str(e)}), 400)
    except Exception as e:
        current_app.logger.error(f"Error fetching menu: {e}")
        return make_response(jsonify({'error': 'Internal Server Error'}), 500)


@menu_bp.route('/best-seller', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_best_seller():
    try:
        # Lấy giá trị tham số limit từ query string và kiểm tra tính hợp lệ
        limit = request.args.get('limit', default=5, type=int)
        target_lang = request.args.get('target_lang')  # lấy ngôn ngữ đích nếu có
        # Kiểm tra xem giá trị limit có hợp lý không
        if limit <= 0 or limit > 100:  # Giới hạn số lượng sản phẩm tối đa là 100
            current_app.logger.warning(f"Invalid limit value: {limit}. Must be between 1 and 100.")
            raise BadRequest("Invalid limit value. Must be between 1 and 100.")

        # Kết nối đến database
        conn = get_connection()
        cursor = conn.cursor()

        # SQL query với LIMIT an toàn, không sử dụng f-string
        sql = """
            SELECT 
                mn.id, 
                mn.name, 
                mn.price, 
                mn.description, 
                mn.image, 
                SUM(od.quantity) AS total_quantity
            FROM menu_items mn
            JOIN order_items od ON od.menu_item_id = mn.id
            JOIN orders o ON o.id = od.order_id
            WHERE mn.is_active = 1 AND o.status = 'completed'
            GROUP BY mn.id, mn.name, mn.price, mn.description, mn.image
            ORDER BY total_quantity DESC
            LIMIT %s;  # Sử dụng parameterized query để tránh SQL Injection
        """
        current_app.logger.info(f"Fetching best sellers with limit={limit}")
        cursor.execute(sql, (limit,))  # Truyền giá trị limit như một tham số an toàn
        rows = cursor.fetchall()
        conn.close()

        # Đưa kết quả vào định dạng JSON
        result = [{
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'description': row[3],
            'image': row[4],
            'total_quantity': row[5]
        } for row in rows]
        if target_lang:
            current_app.logger.info(f"Translating best sellers to {target_lang}")
            result = [translate_dict(item, source_lang="en", target_lang=target_lang) for item in result]
        return make_response(jsonify(result), 200)

    except BadRequest as e:
        current_app.logger.error(f"Bad request: {e}")
        return make_response(jsonify({'error': str(e)}), 400)
    except Exception as e:
        current_app.logger.error(f"Error fetching best sellers: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@menu_bp.route('/', methods=['POST'])
@token_required
def add_item(user_info):
    try:
        data = request.get_json()
        current_app.logger.info(f"Adding new item with data: {data}")
        if not data or 'name' not in data or 'price' not in data:
            current_app.logger.warning("Invalid input, 'name' and 'price' are required.")
            return make_response(jsonify({'error': 'Invalid input'}), 400)
        conn = get_connection()
        cursor = conn.cursor()
        create_time = datetime_to_number(datetime.datetime.now())  # Assuming you have a function to convert datetime to number
        sql = "INSERT INTO menu_items (name, price, description, creator, create_time, is_active,menu_type_id) VALUES (%s, %s, %s, 'admin', %s, 1,%s)"
        cursor.execute(sql, (data['name'], data['price'], data['description'], create_time,data['menu_type_id']))
        conn.commit()
        conn.close()
        reset_cache()
        current_app.logger.info("Item added successfully.")
        return make_response(jsonify({'message': 'Item added successfully'}), 201)
    except Exception as e:
        current_app.logger.error(f"Error adding item: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@menu_bp.route('/<int:id>', methods=['GET'])
def get_menu_by_id(id):
    try:
        current_app.logger.info(f"Getting menu item with id: {id}")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, description FROM menu_items WHERE id = %s AND is_active = 1", (id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            result = {
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'description': row[3]
            }
            return make_response(jsonify(result), 200)
        else:
            current_app.logger.warning(f"Item with id {id} not found.")
            return make_response(jsonify({'message': 'Item not found'}), 404)
    except Exception as e:
        current_app.logger.error(f"Error fetching menu item by id: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@menu_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_menu_item(id, user_info):
    try:
        data = request.get_json()
        current_app.logger.info(f"Updating item {id} with data: {data}")

        conn = get_connection()
        cursor = conn.cursor()
        sql = "UPDATE menu_items SET name = %s, price = %s, description = %s, modifier = 'admin', modify_time = %s WHERE id = %s AND is_active = 1"
        modify_time = datetime_to_number(datetime.datetime.now())
        cursor.execute(sql, (data['name'], data['price'], data['description'], modify_time, id))
        conn.commit()
        conn.close()
        reset_cache()
        if cursor.rowcount == 0:
            current_app.logger.warning(f"Item {id} not found or not active.")
            return make_response(jsonify({'message': 'Item not found or not active'}), 404)
        current_app.logger.info(f"Item {id} updated successfully.")
        return make_response(jsonify({'message': 'Item updated successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error updating item {id}: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@menu_bp.route('/<int:id>/image', methods=['PUT'])
@token_required
def update_menu_item_image(id,user_info):
    try:
        current_app.logger.info(f"Updating image for item {id}")
        data = request.get_json()
        if not data or 'image_url' not in data:
            return make_response(jsonify({'message': 'image_url is required'}), 400)

        conn = get_connection()
        cursor = conn.cursor()
        sql = """UPDATE menu_items 
                 SET image = %s, modifier = 'admin', modify_time = %s 
                 WHERE id = %s AND is_active = 1"""
        modify_time = datetime_to_number(datetime.datetime.now())
        cursor.execute(sql, (data['image_url'], modify_time, id))
        conn.commit()
        conn.close()
        reset_cache()
        if cursor.rowcount == 0:
            return make_response(jsonify({'message': 'Item not found or not active'}), 404)
        current_app.logger.info(f"Image for item {id} updated successfully.")
        return make_response(jsonify({'message': 'Image updated successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error updating image for item {id}: {e}")
        print(f"Error updating image: {e}")
        return make_response(jsonify({'error': str(e)}), 500)

@menu_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_menu_item(id,user_info):
    try:
        print(f"Deleting item {id}")
        conn = get_connection()
        cursor = conn.cursor()
        sql = "UPDATE menu_items SET is_active = 0, modifier = 'admin', modify_time = %s WHERE id = %s AND is_active = 1"
        modify_time = datetime_to_number(datetime.datetime.now())
        cursor.execute(sql, (modify_time, id))
        conn.commit()
        conn.close()
        reset_cache()
        if cursor.rowcount == 0:
            return make_response(jsonify({'message': 'Item not found or already inactive'}), 404)
        return make_response(jsonify({'message': 'Item deleted successfully'}), 200)
    except Exception as e:
        print(f"Error deleting item: {e}")
        return make_response(jsonify({'error': str(e)}), 500)
