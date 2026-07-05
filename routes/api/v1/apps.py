from flask import Blueprint, request, jsonify, send_file
from models import scan_apps, load_apps_config, save_apps_config
import os
import shutil
import zipfile
import io
from datetime import datetime
from config import DEFAULT_APPS_DIR
from utils import safe_extract_zip, has_html_files

apps_bp = Blueprint('apps', __name__)


@apps_bp.route('/', methods=['GET'])
def list_apps():
    """获取所有应用列表"""
    apps = scan_apps()
    return jsonify(apps)


@apps_bp.route('/<app_id>/toggle', methods=['POST'])
def toggle_app(app_id):
    """启用/禁用应用"""
    data = request.json
    enabled = data.get('enabled', True)
    apps_config = load_apps_config()
    if app_id not in apps_config.get('apps', {}):
        apps_config['apps'][app_id] = {}
    apps_config['apps'][app_id]['enabled'] = enabled
    save_apps_config(apps_config)
    return jsonify({'status': 'ok', 'enabled': enabled})


@apps_bp.route('/batch', methods=['POST'])
def batch_toggle():
    """批量启用/禁用"""
    data = request.json
    ids = data.get('ids', [])
    enabled = data.get('enabled', True)
    apps_config = load_apps_config()
    for app_id in ids:
        if app_id not in apps_config.get('apps', {}):
            apps_config['apps'][app_id] = {}
        apps_config['apps'][app_id]['enabled'] = enabled
    save_apps_config(apps_config)
    return jsonify({'status': 'ok'})


@apps_bp.route('/batch', methods=['DELETE'])
def batch_delete():
    """批量删除应用"""
    data = request.json
    ids = data.get('ids', [])
    for app_id in ids:
        app_path = os.path.join(DEFAULT_APPS_DIR, app_id)
        if os.path.exists(app_path):
            shutil.rmtree(app_path)
    apps_config = load_apps_config()
    for app_id in ids:
        if app_id in apps_config.get('apps', {}):
            del apps_config['apps'][app_id]
    save_apps_config(apps_config)
    return jsonify({'status': 'ok'})


@apps_bp.route('/<app_id>', methods=['DELETE'])
def delete_app(app_id):
    """删除单个应用"""
    app_path = os.path.join(DEFAULT_APPS_DIR, app_id)
    if os.path.exists(app_path):
        shutil.rmtree(app_path)
    apps_config = load_apps_config()
    if app_id in apps_config.get('apps', {}):
        del apps_config['apps'][app_id]
    save_apps_config(apps_config)
    return jsonify({'status': 'ok'})


@apps_bp.route('/<app_id>/export')
def export_app(app_id):
    """导出应用为 ZIP 包"""
    app_path = os.path.join(DEFAULT_APPS_DIR, app_id)
    if not os.path.exists(app_path):
        return jsonify({'error': '应用不存在'}), 404
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(app_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, app_path)
                zf.write(file_path, arcname)
    memory_file.seek(0)
    return send_file(
        memory_file,
        download_name=app_id + '.zip',
        as_attachment=True,
        mimetype='application/zip'
    )


@apps_bp.route('/import', methods=['POST'])
def import_app():
    """导入 ZIP 应用包（限制 50 MB）"""
    # 限制上传文件大小（50 MB）
    if request.content_length and request.content_length > 50 * 1024 * 1024:
        return jsonify({'error': '文件过大，请压缩后重试（最大 50 MB）'}), 413

    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        return jsonify({'error': '请上传 zip 文件'}), 400

    try:
        app_name = os.path.splitext(file.filename)[0]
        target_path = os.path.join(DEFAULT_APPS_DIR, app_name)

        # 如果已存在，添加时间戳后缀
        if os.path.exists(target_path):
            app_name = app_name + '_' + datetime.now().strftime('%Y%m%d%H%M%S')
            target_path = os.path.join(DEFAULT_APPS_DIR, app_name)

        # 安全解压
        safe_extract_zip(file, target_path)

        # 递归检查是否存在 HTML 文件
        if not has_html_files(target_path):
            shutil.rmtree(target_path)
            return jsonify({'error': 'zip 中未找到 HTML 文件'}), 400

        # 确保 app.json 存在
        if not os.path.exists(os.path.join(target_path, 'app.json')):
            import json
            with open(os.path.join(target_path, 'app.json'), 'w', encoding='utf-8') as f:
                json.dump({'name': app_name, 'entry': 'index.html'}, f, ensure_ascii=False, indent=2)

        return jsonify({'status': 'ok', 'app_id': app_name})

    except Exception as e:
        return jsonify({'error': str(e)}), 500