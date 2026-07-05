from flask import Blueprint, jsonify
from models import scan_apps, load_apps_config
from datetime import datetime
import json
import os
from config import DATA_DIR, DEFAULT_APPS_DIR

health_bp = Blueprint('health', __name__)
HEALTH_PATH = os.path.join(DATA_DIR, 'health.json')

def load_health_data():
    if os.path.exists(HEALTH_PATH):
        with open(HEALTH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_health_data(data):
    with open(HEALTH_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_app_health(app_id, entry='index.html'):
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    if not os.path.exists(app_dir):
        return {'status': 'error', 'message': '应用目录不存在'}

    entry_path = os.path.join(app_dir, entry)
    if not os.path.exists(entry_path):
        return {'status': 'unhealthy', 'message': f'入口文件 {entry} 不存在'}

    apps_config = load_apps_config()
    if not apps_config.get('apps', {}).get(app_id, {}).get('enabled', True):
        return {'status': 'disabled', 'message': '应用已禁用'}

    return {'status': 'healthy', 'message': '正常'}

@health_bp.route('/check/<app_id>')
def check_health(app_id):
    apps = scan_apps()
    app = next((a for a in apps if a['id'] == app_id), None)
    if not app:
        return jsonify({'error': '应用不存在'}), 404

    result = check_app_health(app_id, app.get('entry', 'index.html'))
    data = load_health_data()
    data[app_id] = {
        **result,
        'last_check': datetime.now().isoformat(),
        'app_name': app['name']
    }
    save_health_data(data)
    return jsonify(data[app_id])

@health_bp.route('/check/all')
def check_all_health():
    apps = scan_apps()
    results = {}
    for app in apps:
        result = check_app_health(app['id'], app.get('entry', 'index.html'))
        results[app['id']] = {
            **result,
            'last_check': datetime.now().isoformat(),
            'app_name': app['name']
        }
    save_health_data(results)
    return jsonify({
        'total': len(results),
        'healthy': sum(1 for r in results.values() if r['status'] == 'healthy'),
        'unhealthy': sum(1 for r in results.values() if r['status'] == 'unhealthy'),
        'disabled': sum(1 for r in results.values() if r['status'] == 'disabled'),
        'error': sum(1 for r in results.values() if r['status'] == 'error'),
        'details': results
    })

@health_bp.route('/status')
def health_status():
    data = load_health_data()
    return jsonify({
        'total': len(data),
        'healthy': sum(1 for r in data.values() if r.get('status') == 'healthy'),
        'unhealthy': sum(1 for r in data.values() if r.get('status') == 'unhealthy'),
        'disabled': sum(1 for r in data.values() if r.get('status') == 'disabled'),
        'error': sum(1 for r in data.values() if r.get('status') == 'error'),
        'details': data
    })