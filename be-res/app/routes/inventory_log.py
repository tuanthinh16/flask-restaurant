from flask import Blueprint, request, jsonify, make_response, current_app
from app.db import get_connection
import datetime
from utils.translateDict import translate_dict
from utils.dateTimeConvert import datetime_to_number
from utils.tokenRequired import token_required

inventory_logs_bp = Blueprint('inventory_logs', __name__)

@inventory_logs_bp.route('/', methods=['GET'])
@token_required
def get_logs(user_info):
    try:
        log_id = request.args.get('id', type=int)
        limit = request.args.get('limit', type=int)
        start = request.args.get('start', type=int)
        target_lang = request.args.get('target_lang')  # Ngôn ngữ đích nếu có
        conn = get_connection()
        cursor = conn.cursor()

        if log_id:
            cursor.execute("SELECT * FROM inventory_logs WHERE id = %s AND is_active = 1", (log_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                current_app.logger.warning(f"Log with ID {log_id} not found.")
                return make_response(jsonify({'message': 'Log not found'}), 404)

            keys = [
                'id', 'creator', 'create_time', 'modifier', 'modify_time', 'is_active',
                'inventory_id', 'change_type', 'quantity', 'status', 'note', 'log_time'
            ]
            if target_lang:
                result = translate_dict(result, source_lang="en", target_lang=target_lang)

            current_app.logger.info(f"Fetched log with ID {log_id} successfully.")
            return jsonify(dict(zip(keys, row)))

        sql = "SELECT * FROM inventory_logs WHERE is_active = 1 ORDER BY log_time DESC"
        params = []
        if limit is not None and start is not None:
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, start])

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        keys = [
            'id', 'creator', 'create_time', 'modifier', 'modify_time', 'is_active',
            'inventory_id', 'change_type', 'quantity', 'status', 'note', 'log_time'
        ]
        result = [dict(zip(keys, row)) for row in rows]
        if target_lang:
            result = [translate_dict(item, source_lang="en", target_lang=target_lang) for item in result]

        current_app.logger.info("Fetched inventory logs successfully.")
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error while fetching inventory logs: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@inventory_logs_bp.route('/', methods=['POST'])
@token_required
def add_log(user_info):
    try:
        data = request.get_json()
        now = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO inventory_logs (
                creator, create_time, is_active,
                inventory_id, change_type, quantity, status, note, log_time
            ) VALUES (%s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            user_info['username'],
            now,
            data['inventory_id'],
            data['change_type'],
            data['quantity'],
            data.get('status', 'pending'),
            data.get('note', ''),
            now
        ))
        conn.commit()
        conn.close()

        current_app.logger.info(f"Log added successfully by {user_info['username']}.")
        return make_response(jsonify({'message': 'Log added successfully'}), 201)

    except Exception as e:
        current_app.logger.error(f"Error while adding log: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@inventory_logs_bp.route('/approval/<int:id>', methods=['POST', 'PUT'])
@token_required
def approve(id, user_info):
    try:
        now = datetime_to_number(datetime.datetime.now())
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE inventory_logs
            SET status = 'approved', modifier = %s, modify_time = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (user_info['username'], now, id))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            current_app.logger.warning(f"Log with ID {id} not found or already inactive.")
            return make_response(jsonify({'message': 'Log not found or already inactive'}), 404)

        current_app.logger.info(f"Log with ID {id} approved successfully by {user_info['username']}.")
        return make_response(jsonify({'message': 'Log approved successfully'}), 200)

    except Exception as e:
        current_app.logger.error(f"Error while approving log with ID {id}: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)
