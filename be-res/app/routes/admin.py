from flask import Blueprint, jsonify, make_response, current_app
from app.db import get_connection
from utils.cacheDB import reset_database
from utils.tokenRequired import token_required
from app.extensions import cache, limiter

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/reset-cache', methods=['POST'])
@limiter.limit("5 per minute")
@token_required
def reset_cache_route(user_info):
    try:
        current_app.logger.debug(f"Resetting cache by user: {user_info['username']}")
        result = reset_cache()
        deleted = reset_database()
        current_app.logger.info(f"Cache cleared successfully. Deleted {deleted} rows from database.")
        return make_response(jsonify({"cacheDB": result, "trans_cache": deleted}), 200)
    except Exception as e:
        current_app.logger.error(f"Error resetting cache: {e}")
        return make_response(jsonify({"error": str(e)}), 500)


def reset_cache():
    try:
        cache.clear()
        return {'message': 'Cache cleared successfully'}
    except Exception as e:
        return {'error': str(e)}

@admin_bp.route('/dashboard')
@token_required
def get_total_data(user_info):
    try:
        # Kết nối đến database
        conn = get_connection()
        cursor = conn.cursor()

        # Tổng số bàn
        cursor.execute("SELECT COUNT(*) FROM tables where is_active = 1")
        total_tables = cursor.fetchone()[0]

        # Tổng số món
        cursor.execute("SELECT COUNT(*) FROM menu_items where is_active = 1")
        total_dishes = cursor.fetchone()[0]

        # Tổng số người dùng
        cursor.execute("SELECT COUNT(*) FROM users where is_active = 1")
        total_users = cursor.fetchone()[0]

        # Doanh thu
        cursor.execute("SELECT IFNULL(SUM(total), 0) FROM orders where is_active = 1")
        revenue = cursor.fetchone()[0]

        # Biểu đồ doanh thu theo tháng
        revenue_chart_query = """
            SELECT DATE_FORMAT(FROM_UNIXTIME(create_time / 1000), '%Y-%m') AS month,
                   SUM(total) AS total
            FROM orders
            GROUP BY month
            ORDER BY month
        """
        cursor.execute(revenue_chart_query)
        revenue_chart = [{'month': row[0], 'total': row[1]} for row in cursor.fetchall()]

        # Món ăn phổ biến
        popular_dishes_query = """
            SELECT mi.name, COUNT(od.id) AS count
            FROM order_items od
            JOIN menu_items mi ON od.menu_item_id = mi.id
            where od.is_active = 1
            GROUP BY mi.name
            ORDER BY count DESC
            LIMIT 5
        """
        cursor.execute(popular_dishes_query)
        popular_dishes = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]

        current_app.logger.info(f"Fetched dashboard data: Total tables {total_tables}, total dishes {total_dishes}, total users {total_users}, revenue {revenue}")

        return jsonify({
            'totalTables': total_tables,
            'totalDishes': total_dishes,
            'totalUsers': total_users,
            'revenue': str(revenue),
            'revenueChart': revenue_chart,
            'popularDishes': popular_dishes
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard data: {e}")
        return jsonify({'error': str(e)}), 500
