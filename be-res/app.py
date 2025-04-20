from flask_caching import Cache
from app import create_app
from flask_limiter import Limiter

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port=5000)
