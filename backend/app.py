from flask import Flask, request, jsonify, send_from_directory, send_file, make_response
from flask_cors import CORS
import database, re, os, logging, mimetypes
from pathlib import Path
from itertools import islice
from functools import wraps

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

IMAGES_PATH = r"E:\牛头人的美图"
VIDEO_PATH = r"E:\牛头人的美图\牛头人视频\indexvideo20250105.mp4"
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    SEND_FILE_MAX_AGE_DEFAULT=43200
)

def get_all_images():
    cache_key = f'images_cache_{os.path.getmtime(IMAGES_PATH)}'
    if hasattr(get_all_images, cache_key):
        return getattr(get_all_images, cache_key)

    images = []
    try:
        for root, _, files in os.walk(IMAGES_PATH):
            for file in files:
                if Path(file).suffix.lower() in ALLOWED_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                        relative_path = os.path.relpath(file_path, IMAGES_PATH)
                        images.append({
                            'path': relative_path,
                            'size': os.path.getsize(file_path),
                            'mime': mimetypes.guess_type(file_path)[0]
                        })
        images.sort(key=lambda x: x['size'], reverse=True)
        setattr(get_all_images, cache_key, images)
        return images
    except Exception as e:
        logger.error(f"Error scanning directory: {str(e)}")
        return []

@app.route('/api/images')
def list_images():
    try:
        page = max(1, request.args.get('page', 1, type=int))
        per_page = 270
        all_images = get_all_images()
        total = len(all_images)
        total_pages = max(1, (total + per_page - 1) // per_page)
        images = list(islice(all_images, (page-1)*per_page, page*per_page))
        return jsonify({'success': True, 'data': {
            'images': images, 'total': total,
            'current_page': min(page, total_pages),
            'total_pages': total_pages
        }})
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        return jsonify({'success': False, 'message': '获取失败'}), 500

@app.route('/api/images/<path:image_path>')
def serve_image(image_path):
    try:
        full_path = os.path.abspath(os.path.join(IMAGES_PATH, image_path))
        if not full_path.startswith(os.path.abspath(IMAGES_PATH)):
            return jsonify({'success': False, 'message': '无效路径'}), 403
        
        response = send_file(full_path, mimetype=mimetypes.guess_type(full_path)[0],
                           conditional=True)
        response.headers.update({
            'Cache-Control': 'public, max-age=43200',
            'ETag': f"{os.path.getmtime(full_path)}:{os.path.getsize(full_path)}"
        })
        return response
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        return jsonify({'success': False, 'message': '加载失败'}), 500

@app.route('/api/video/background')
def serve_background_video():
    try:
        response = send_file(VIDEO_PATH, mimetype='video/mp4', conditional=True)
        response.headers.update({
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=43200'
        })
        return response
    except Exception as e:
        logger.error(f"Error serving video: {str(e)}")
        return jsonify({'success': False, 'message': '视频加载失败'}), 500

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

def validate_input(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            if not username or not password:
                return jsonify({'success': False, 'message': '用户名和密码不能为空'})
            if not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
                return jsonify({'success': False, 'message': '用户名格式错误'})
            if len(password) < 6 or len(password) > 20:
                return jsonify({'success': False, 'message': '密码长度错误'})
            
            return func(username, password)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return jsonify({'success': False, 'message': '服务器错误'})
    return wrapper

@app.route('/api/register', methods=['POST'])
@validate_input
def register(username, password):
    try:
        if database.user_exists(username):
            return jsonify({'success': False, 'message': '用户名已存在'})
        database.add_user(username, password)
        return jsonify({'success': True, 'message': '注册成功'})
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'success': False, 'message': '注册失败'})

@app.route('/api/login', methods=['POST'])
@validate_input
def login(username, password):
    try:
        if database.verify_user(username, password):
            return jsonify({'success': True, 'message': '登录成功'})
        return jsonify({'success': False, 'message': '用户名或密码错误'})
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': '登录失败'})

if __name__ == '__main__':
    database.init_db()
    app.run(debug=True) 
