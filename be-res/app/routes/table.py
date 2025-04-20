import datetime
from flask import Blueprint, request, jsonify, make_response, current_app
from app.db import get_connection
from app.routes.admin import reset_cache
from utils.dateTimeConvert import datetime_to_number
from flask_cors import CORS
from app.extensions import cache
from utils.tokenRequired import token_required

tables_bp = Blueprint('tables', __name__)
CORS(tables_bp, origins="*")

@tables_bp.route('/', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_tables():
    try:
        table_id = request.args.get('id', type=int)
        start = request.args.get('start', type=int)
        limit = request.args.get('limit', type=int)

        current_app.logger.debug(f"Fetching tables with table_id: {table_id}, start: {start}, limit: {limit}")

        conn = get_connection()
        cursor = conn.cursor()

        if table_id:
            cursor.execute("SELECT id, table_number, capacity FROM tables WHERE id = %s AND is_active = 1", (table_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                current_app.logger.info(f"Table found: {row}")
                return make_response(jsonify({
                    'id': row[0],
                    'table_number': row[1],
                    'capacity': row[2]
                }), 200)
            else:
                current_app.logger.warning(f"Table with id {table_id} not found.")
                return make_response(jsonify({'message': 'Table not found'}), 404)
        else:
            sql = "SELECT id, table_number, capacity FROM tables WHERE is_active = 1"
            params = []

            if limit is not None and start is not None:
                sql += " LIMIT %s OFFSET %s"
                params.extend([limit, start])

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            result = [{
                'id': row[0],
                'table_number': row[1],
                'capacity': row[2]
            } for row in rows]
            current_app.logger.info(f"Fetched {len(rows)} tables")
            return make_response(jsonify(result), 200)
    except Exception as e:
        current_app.logger.error(f"Error fetching tables: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@tables_bp.route('/', methods=['POST'])
@token_required
def add_table(user_info):
    try:
        data = request.get_json()
        current_app.logger.debug(f"Creating table with data: {data}")

        create_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO tables (creator, create_time, is_active, table_number, capacity)
            VALUES (%s, %s, 1, %s, %s)
        """
        cursor.execute(sql, (
            user_info['username'],
            create_time,
            data['table_number'],
            data['capacity']
        ))
        conn.commit()
        conn.close()
        reset_cache()

        current_app.logger.info(f"Table created successfully by {user_info['username']}")
        return make_response(jsonify({'message': 'Table created successfully'}), 201)
    except Exception as e:
        current_app.logger.error(f"Error creating table: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@tables_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_table(id, user_info):
    try:
        data = request.get_json()
        current_app.logger.debug(f"Updating table {id} with data: {data}")

        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE tables SET table_number = %s, capacity = %s, modifier = 'admin', modify_time = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (
            data['table_number'],
            data['capacity'],
            modify_time,
            id
        ))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Table with id {id} not found or not active.")
            return make_response(jsonify({'message': 'Table not found or not active'}), 404)
        
        current_app.logger.info(f"Table {id} updated successfully.")
        return make_response(jsonify({'message': 'Table updated successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error updating table {id}: {e}")
        return make_response(jsonify({'error': str(e)}), 500)


@tables_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_table(id, user_info):
    try:
        if user_info['role'] != 'admin':
            current_app.logger.warning(f"Permission denied for user {user_info['username']} to delete table {id}")
            return make_response(jsonify({'message': 'Permission denied'}), 403)

        current_app.logger.debug(f"Deleting table {id} by {user_info['username']}")
        modify_time = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = "UPDATE tables SET is_active = 0, modifier = 'admin', modify_time = %s WHERE id = %s AND is_active = 1"
        cursor.execute(sql, (modify_time, id))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Table with id {id} not found or already inactive.")
            return make_response(jsonify({'message': 'Table not found or already inactive'}), 404)

        current_app.logger.info(f"Table {id} deleted successfully.")
        return make_response(jsonify({'message': 'Table deleted successfully'}), 200)
    except Exception as e:
        current_app.logger.error(f"Error deleting table {id}: {e}")
        return make_response(jsonify({'error': str(e)}), 500)
