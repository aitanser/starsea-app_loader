import json
import os
from config import (
    ADMIN_CONFIG_PATH, APP_CONFIG_PATH, FAVORITES_PATH,
    NOTE_PATH, CONFIG_PATH, DEFAULT_APPS_DIR, DATA_DIR
)

def load_admin_password():
    if os.path.exists(ADMIN_CONFIG_PATH):
        with open(ADMIN_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get('password', 'admin123')
    with open(ADMIN_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({'password': 'admin123'}, f, ensure_ascii=False, indent=2)
    return 'admin123'

def save_admin_password(new_password):
    with open(ADMIN_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({'password': new_password}, f, ensure_ascii=False, indent=2)

def load_favorites():
    if os.path.exists(FAVORITES_PATH):
        with open(FAVORITES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get('favorites', [])
    return []

def save_favorites(favorites):
    with open(FAVORITES_PATH, 'w', encoding='utf-8') as f:
        json.dump({'favorites': favorites}, f, ensure_ascii=False, indent=2)

def load_notes():
    if os.path.exists(NOTE_PATH):
        with open(NOTE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get('notes', {})
    return {}

def save_notes(notes):
    with open(NOTE_PATH, 'w', encoding='utf-8') as f:
        json.dump({'notes': notes}, f, ensure_ascii=False, indent=2)

def load_framework_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'port': 8000, 'apps_dir': DEFAULT_APPS_DIR, 'version': '1.0'}

def save_framework_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_apps_config():
    if os.path.exists(APP_CONFIG_PATH):
        with open(APP_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'apps': {}}

def save_apps_config(config):
    with open(APP_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_app_config(app_id):
    """
    读取应用目录下的 app.json 配置
    返回字典，包含 name, entry, type, fallback 等字段
    若文件不存在或解析失败，返回空字典
    """
    config_path = os.path.join(DEFAULT_APPS_DIR, app_id, 'app.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def scan_apps(apps_dir=None):
    if apps_dir is None:
        apps_dir = DEFAULT_APPS_DIR
    apps = []
    if not os.path.exists(apps_dir):
        return apps
    apps_config = load_apps_config()
    for item in os.listdir(apps_dir):
        path = os.path.join(apps_dir, item)
        if not os.path.isdir(path) or item.startswith('_'):
            continue
        html_files = [f for f in os.listdir(path) if f.endswith('.html')]
        if not html_files:
            continue
        config = {}
        config_path = os.path.join(path, 'app.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        app_cfg = apps_config.get('apps', {}).get(item, {})
        entry = config.get('entry', 'index.html' if 'index.html' in html_files else html_files[0])
        # 新增：读取 type 和 fallback
        app_type = config.get('type', 'mpa')
        fallback = config.get('fallback', entry)
        apps.append({
            'name': config.get('name', item),
            'id': item,
            'path': path,
            'entry': entry,
            'description': config.get('description', ''),
            'icon_class': config.get('icon_class', 'fa-folder'),
            'category': config.get('category', '未分类'),
            'tags': config.get('tags', []),
            'html_files': html_files,
            'version': config.get('version', '1.0'),
            'enabled': app_cfg.get('enabled', True),
            'created': app_cfg.get('created', ''),
            'last_accessed': app_cfg.get('last_accessed', ''),
            'access_count': app_cfg.get('access_count', 0),
            'app_type': app_type,      # 新增
            'fallback': fallback       # 新增
        })
    return apps

# ==================== 用户管理 ====================
USER_PATH = os.path.join(DATA_DIR, 'users.json')

def load_users():
    if os.path.exists(USER_PATH):
        with open(USER_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for username, info in data.items():
                if 'role' not in info:
                    info['role'] = 'user'
            return data
    else:
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        default_admin = {
            "admin": {
                "password_hash": generate_password_hash("admin123"),
                "role": "admin",
                "created": datetime.now().isoformat()
            }
        }
        save_users(default_admin)
        return default_admin

def save_users(users):
    with open(USER_PATH, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_user(username, password_hash, role='user'):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        'password_hash': password_hash,
        'role': role,
        'created': __import__('datetime').datetime.now().isoformat()
    }
    save_users(users)
    return True