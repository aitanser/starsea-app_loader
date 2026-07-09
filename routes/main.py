#!/usr/bin/env python3
# main.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, render_template, send_from_directory, request, redirect, session, make_response
from models import scan_apps, load_favorites, load_apps_config, save_apps_config, load_app_config
from utils import get_local_ip, get_recent_apps, log_access, record_user_app_access
from config import DEFAULT_PORT, DEFAULT_APPS_DIR
from license import LicenseManager
import os
import json
import time
from datetime import datetime

main_bp = Blueprint('main', __name__)

_visit_cache = {}
_VISIT_CACHE_EXPIRE = 3
_VISIT_CACHE_MAX = 2000

def should_count_visit(app_id, client_ip):
    key = (app_id, client_ip)
    now = time.time()
    if key in _visit_cache:
        if now - _visit_cache[key] < _VISIT_CACHE_EXPIRE:
            return False
    _visit_cache[key] = now
    if len(_visit_cache) > _VISIT_CACHE_MAX:
        sorted_items = sorted(_visit_cache.items(), key=lambda x: x[1])
        for k, _ in sorted_items[:len(_visit_cache)//2]:
            del _visit_cache[k]
    return True

@main_bp.route('/')
def index():
    apps = scan_apps()
    favorites = load_favorites()
    categories = sorted(set(a.get('category', '未分类') for a in apps))
    all_tags = sorted(set(tag for a in apps for tag in a.get('tags', [])))
    recent_apps = get_recent_apps(6)

    try:
        from routes.api.v1.rating import load_ratings
        ratings = load_ratings()
    except:
        ratings = {}
    for app in apps:
        app['is_favorite'] = app['id'] in favorites
        r = ratings.get(app['id'], {'total': 0, 'count': 0})
        app['avg_rating'] = round(r['total'] / r['count'], 1) if r['count'] > 0 else 0
        app['rating_count'] = r['count']

    current_user = session.get('user')
    current_role = session.get('role', 'user')
    license_info = LicenseManager.get_quota_info()

    return render_template('index.html',
                           apps=apps,
                           categories=categories,
                           all_tags=all_tags,
                           favorites=favorites,
                           recent_apps=recent_apps,
                           port=DEFAULT_PORT,
                           ip=get_local_ip(),
                           apps_dir=DEFAULT_APPS_DIR,
                           current_user=current_user,
                           current_role=current_role,
                           license=license_info)

@main_bp.route('/app/<app_id>/<path:filename>')
def serve_app_file(app_id, filename):
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    safe_path = os.path.abspath(os.path.join(app_dir, filename))
    if not safe_path.startswith(os.path.abspath(app_dir)):
        return "Forbidden", 403

    config = load_app_config(app_id)
    app_type = config.get('type', 'mpa')
    fallback = config.get('fallback', config.get('entry', 'index.html'))

    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    STATIC_EXTS = {
        '.css', '.js', '.map',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.avif', '.bmp',
        '.woff', '.woff2', '.ttf', '.eot', '.otf',
        '.mp3', '.mp4', '.webm', '.ogg',
        '.json', '.xml'
    }

    if not os.path.exists(safe_path):
        if app_type == 'spa' and ext not in STATIC_EXTS:
            fallback_path = os.path.join(app_dir, fallback)
            if os.path.exists(fallback_path):
                log_access(request, app_id)
                return send_from_directory(app_dir, fallback)
        return "File not found", 404

    log_access(request, app_id)

    is_html = filename.endswith('.html') or filename.endswith('.htm')
    client_ip = request.remote_addr
    should_count = is_html and should_count_visit(app_id, client_ip)

    if should_count:
        user = session.get('user')
        if user:
            record_user_app_access(user, app_id)

        try:
            apps_config = load_apps_config()
            if app_id in apps_config.get('apps', {}):
                apps_config['apps'][app_id]['last_accessed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                apps_config['apps'][app_id]['access_count'] = apps_config['apps'][app_id].get('access_count', 0) + 1
                save_apps_config(apps_config)
            else:
                apps_config['apps'][app_id] = {
                    'enabled': True,
                    'last_accessed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'access_count': 1
                }
                save_apps_config(apps_config)
        except Exception as e:
            print(f"[统计错误] {e}")

    response = make_response(send_from_directory(app_dir, filename))
    if ext in STATIC_EXTS:
        response.headers['Cache-Control'] = 'public, max-age=86400'
    else:
        response.headers['Cache-Control'] = 'no-cache, must-revalidate'
    return response

@main_bp.route('/app/<app_id>/')
def serve_app_index(app_id):
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    config_path = os.path.join(app_dir, 'app.json')
    entry = 'index.html'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                entry = config.get('entry', 'index.html')
        except:
            pass
    return redirect(f'/app/{app_id}/{entry}')