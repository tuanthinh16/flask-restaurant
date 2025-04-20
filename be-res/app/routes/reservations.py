from flask import Blueprint, request, jsonify, make_response, current_app
from app.db import get_connection
from utils.dateTimeConvert import datetime_to_number
import datetime
from utils.tokenRequired import token_required

reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('/', methods=['GET'])
def get_reservations():
    try:
        reservation_id = request.args.get('id', type=int)
        start = request.args.get('start', type=int)
        limit = request.args.get('limit', type=int)

        current_app.logger.info("Fetching reservations with id: %s, start: %s, limit: %s", reservation_id, start, limit)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if reservation_id:
            cursor.execute("SELECT * FROM reservations WHERE id = %s AND is_active = 1", (reservation_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                current_app.logger.warning("Reservation with id %s not found", reservation_id)
                return make_response(jsonify({'message': 'Reservation not found'}), 404)
            return jsonify(row)

        sql = "SELECT * FROM reservations WHERE is_active = 1 ORDER BY reservation_time DESC"
        params = []
        if limit is not None and start is not None:
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, start])

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        current_app.logger.info("Fetched %d reservations", len(rows))
        return jsonify(rows)
    except Exception as e:
        current_app.logger.error("Error fetching reservations: %s", str(e))
        return make_response(jsonify({'error': str(e)}), 500)


@reservations_bp.route('/', methods=['POST'])
def add_reservation():
    try:
        data = request.get_json()
        now = datetime_to_number(datetime.datetime.now())
        current_app.logger.info("Adding reservation: %s", data)
        
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO reservations (
                creator, create_time, is_active,
                table_id, customer_name, reservation_time, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            'admin',
            now,
            data['table_id'],
            data['customer_name'],
            data['reservation_time'],
            data.get('status', 'pending')
        ))
        conn.commit()
        conn.close()
        current_app.logger.info("Reservation created successfully")
        return make_response(jsonify({'message': 'Reservation created successfully'}), 201)
    except Exception as e:
        current_app.logger.error("Error creating reservation: %s", str(e))
        return make_response(jsonify({'error': str(e)}), 500)


@reservations_bp.route('/<int:id>', methods=['PUT'])
@token_required
def update_reservation(id, user_info):
    try:
        data = request.get_json()
        now = datetime_to_number(datetime.datetime.now())
        current_app.logger.info("Updating reservation with id: %d", id)
        
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE reservations SET
                modifier = %s,
                modify_time = %s,
                table_id = %s,
                customer_name = %s,
                reservation_time = %s,
                status = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (
            user_info['username'],
            now,
            data['table_id'],
            data['customer_name'],
            data['reservation_time'],
            data.get('status', 'pending'),
            id
        ))
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.warning("Reservation with id %d not found", id)
            return make_response(jsonify({'message': 'Reservation not found'}), 404)
        current_app.logger.info("Reservation with id %d updated successfully", id)
        return make_response(jsonify({'message': 'Reservation updated successfully'}), 200)
    except Exception as e:
        current_app.logger.error("Error updating reservation with id %d: %s", id, str(e))
        return make_response(jsonify({'error': str(e)}), 500)


@reservations_bp.route('/approval/<int:id>', methods=['PUT', 'POST'])
@token_required
def update_reservation_approval(id, user_info):
    try:
        now = datetime_to_number(datetime.datetime.now())
        current_app.logger.info("Approving reservation with id: %d", id)
        
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE reservations SET
                modifier = %s,
                modify_time = %s,
                status = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (
            user_info['username'],
            now,
            'approved',
            id
        ))
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.warning("Reservation with id %d not found", id)
            return make_response(jsonify({'message': 'Reservation not found'}), 404)
        current_app.logger.info("Reservation with id %d approved successfully", id)
        return make_response(jsonify({'message': 'Reservation approved successfully'}), 200)
    except Exception as e:
        current_app.logger.error("Error approving reservation with id %d: %s", id, str(e))
        return make_response(jsonify({'error': str(e)}), 500)


@reservations_bp.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_reservation(id, user_info):
    try:
        now = datetime_to_number(datetime.datetime.now())
        current_app.logger.info("Deleting reservation with id: %d", id)
        
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE reservations SET
                is_active = 0,
                modifier = %s,
                modify_time = %s
            WHERE id = %s AND is_active = 1
        """
        cursor.execute(sql, (user_info['username'], now, id))
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            current_app.logger.warning("Reservation with id %d not found", id)
            return make_response(jsonify({'message': 'Reservation not found'}), 404)
        current_app.logger.info("Reservation with id %d deleted successfully", id)
        return make_response(jsonify({'message': 'Reservation deleted successfully'}), 200)
    except Exception as e:
        current_app.logger.error("Error deleting reservation with id %d: %s", id, str(e))
        return make_response(jsonify({'error': str(e)}), 500)
