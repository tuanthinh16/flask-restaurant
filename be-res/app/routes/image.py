import datetime
import os
from flask import Blueprint, current_app, make_response, request, jsonify
from app.db import get_connection
from utils.tokenRequired import is_admin, token_required
from utils.dateTimeConvert import datetime_to_number
from dotenv import load_dotenv

load_dotenv() 

import cloudinary
import cloudinary.uploader
import cloudinary.api

img_bp = Blueprint('image', __name__)
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
api_key = os.getenv('CLOUDINARY_API_KEY')
api_secret = os.getenv('CLOUDINARY_API_SECRET')
upload_preset = os.getenv('CLOUDINARY_UPLOAD_PRESET')
cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret
)

@img_bp.route('/upload', methods=['POST'])
@token_required 
def upload_to_cloud(user_info):
    # Log toàn bộ headers và form data
    current_app.logger.debug(f"Request Headers: {dict(request.headers)}")
    current_app.logger.debug(f"Form data: {request.form.to_dict()}")
    current_app.logger.debug(f"Files: {dict(request.files)}")
    current_app.logger.debug(f"User info: {user_info}")
    
    # Kiểm tra config Cloudinary
    current_app.logger.debug(f"Cloudinary Configuration - Cloud name: {cloud_name}, Upload preset: {upload_preset}")
    
    if not all([cloud_name, upload_preset]):
        error_msg = "Missing Cloudinary configuration!"
        current_app.logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

    # Validate input
    file = request.files.get('file')
    menu_id = request.form.get('public_id')
    
    current_app.logger.debug(f"File received: {'Yes' if file else 'No'}, Filename: {file.filename if file else 'None'}, Menu ID: {menu_id}")
    
    if not file:
        error_msg = "No file uploaded!"
        current_app.logger.error(error_msg)
        return jsonify({'error': error_msg}), 400
        
    if not menu_id:
        error_msg = "Missing menu_id!"
        current_app.logger.error(error_msg) 
        return jsonify({'error': error_msg}), 400

    # Kiểm tra file type
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else None
    
    current_app.logger.debug(f"File extension: {file_ext}, Allowed extensions: {ALLOWED_EXTENSIONS}")
    
    if not file_ext or file_ext not in ALLOWED_EXTENSIONS:
        error_msg = f"Invalid file type! Allowed: {ALLOWED_EXTENSIONS}"
        current_app.logger.error(error_msg)
        return jsonify({'error': error_msg}), 400

    # Chuẩn bị upload
    public_id = f"MenuID-{menu_id}"
    upload_options = {
        'public_id': public_id,
        'overwrite': True,
        'upload_preset': upload_preset,
        'resource_type': 'auto'
    }
    
    current_app.logger.debug(f"Upload options: {upload_options}")

    try:
        current_app.logger.debug("Uploading to Cloudinary...")
        upload_result = cloudinary.uploader.upload(file, **upload_options)
        
        current_app.logger.debug(f"Upload result: {upload_result}")
        
        if not upload_result.get('secure_url'):
            error_msg = "Upload succeeded but no secure_url returned!"
            current_app.logger.error(f"{error_msg}, Raw response: {upload_result}")
            return jsonify({'error': error_msg}), 500
            
        current_app.logger.info(f"Upload successful - Public ID: {upload_result['public_id']}, Secure URL: {upload_result['secure_url']}, File size: {upload_result.get('bytes', 'N/A')} bytes")
        
        return jsonify({
            'success': True,
            'public_id': upload_result['public_id'],
            'secure_url': upload_result['secure_url'],
            'details': {
                'format': upload_result.get('format'),
                'width': upload_result.get('width'),
                'height': upload_result.get('height'),
                'size': upload_result.get('bytes')
            }
        }), 200

    except cloudinary.api.Error as e:
        error_msg = f"Cloudinary API Error: {str(e)}"
        current_app.logger.error(f"{error_msg}, Error details: {e.__dict__}")
        return jsonify({'error': error_msg}), 500
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        current_app.logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

# Hàm kiểm tra loại file cho phép
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@img_bp.route('/clean-cloud', methods=['POST'])
@token_required
def clean_unused_images(user_info):
    if not is_admin(user_info):
        current_app.logger.warning(f"User {user_info['username']} tried to access clean-cloud without admin rights.")
        return make_response(jsonify({'message': 'Permission denied'}), 403)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy danh sách menu_items active và các secure_url tương ứng
    cursor.execute("""
        SELECT id, image 
        FROM menu_items 
        WHERE is_active = 1 AND image IS NOT NULL
    """)
    valid_entries = {str(row[0]): row[1] for row in cursor.fetchall()}

    # Lấy danh sách ảnh trong thư mục Menu trên Cloudinary
    resources = []
    next_cursor = None
    while True:
        result = cloudinary.api.resources(
            type="upload",
            folder="Menu",
            max_results=100,
            next_cursor=next_cursor
        )
        resources.extend(result['resources'])
        next_cursor = result.get('next_cursor')
        if not next_cursor:
            break

    to_delete = []
    for img in resources:
        # Chỉ xử lý các ảnh trong thư mục Menu
        if img.get('folder') == 'Menu':
            public_id = img['public_id']
            secure_url = img['secure_url']
            
            # Kiểm tra ảnh có dạng MenuID-<id>
            if public_id.startswith("Menu/MenuID-"):
                menu_id = public_id.split("MenuID-")[-1]
                
                # Kiểm tra 3 điều kiện:
                # 1. ID có trong database không?
                # 2. Nếu có, secure_url có khớp với image_url trong database không?
                # 3. Nếu không khớp hoặc không có ID thì xóa
                if menu_id in valid_entries:
                    if valid_entries[menu_id] != secure_url:
                        to_delete.append(public_id)
                else:
                    to_delete.append(public_id)
            else:
                # Xóa tất cả ảnh không có dạng MenuID-<id>
                to_delete.append(public_id)

    if to_delete:
        cloudinary.api.delete_resources(to_delete)
        current_app.logger.info(f"Deleted {len(to_delete)} unused images from Cloudinary Menu folder.")
    
    current_app.logger.info(f"Total images checked: {len(resources)}, Valid images in DB: {len(valid_entries)}")
    return jsonify({
        'deleted': to_delete,
        'count': len(to_delete),
        'message': f'Deleted {len(to_delete)} unused images from Menu folder',
        'details': {
            'total_images_checked': len(resources),
            'valid_images_in_db': len(valid_entries)
        }
    })
