import pymysql
import os

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'db'),
        user=os.getenv('DB_USER', 'dev'),
        password=os.getenv('DB_PASS', 'devpass'),
        database=os.getenv('DB_NAME', 'restaurant')
    )
