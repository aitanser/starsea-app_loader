from flask import Blueprint, jsonify, request, send_file
from models import scan_apps
from utils import get_access_logs, safe_extract_zip
import os
import io
import zipfile
import shutil
from datetime import datetime
from config import DATA_DIR, LOG_PATH

system_bp = Blueprint('system', __name__)

@system_bp.route('/health')
def health():
    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
    except:
        cpu = mem = disk = 0
    return jsonify({
        'cpu': cpu,
        'memory': mem,
        'disk': disk,
        'app_count': len(scan_apps()),
        'log_size': os.path.getsize(LOG_PATH) if os.path.exists(LOG_PATH) else 0
    })

@system_bp.route('/backup', methods=['POST'])
def backup():
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                if file == 'access.log' or root.endswith('backups'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, DATA_DIR)
                zf.write(file_path, arcname)
    memory_file.seek(0)
    return send_file(memory_file, download_name='backup_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip', as_attachment=True, mimetype='application/zip')

@system_bp.route('/restore', methods=['POST'])
def restore():
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        return jsonify({'error': '请上传 zip 文件'}), 400
    try:
        # 使用安全解压到 DATA_DIR
        safe_extract_zip(file, DATA_DIR)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500