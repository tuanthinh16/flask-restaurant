import os

try:
    with open('secret_key.txt', 'r') as f:
        SECRET_KEY = f.read().strip()
except FileNotFoundError:
    SECRET_KEY = 'thinhvipnghean'  # giá trị mặc định khi không có file
