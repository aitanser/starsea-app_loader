#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# app.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

import os
import sys
import webbrowser
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect
from config import DEFAULT_PORT
from routes import register_blueprints
from utils import get_local_ip
from models import scan_apps, load_users, save_users
from license import LicenseManager
from werkzeug.security import check_password_hash

# ---------- 颜色辅助 ----------
def supports_color():
    return (
        hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
        (os.name == 'nt' or 'TERM' in os.environ)
    )

COLOR = supports_color()
if COLOR:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
else:
    GREEN = CYAN = YELLOW = RED = BOLD = RESET = ''

def cprint(text, color='', bold=False):
    prefix = BOLD if bold else ''
    print(f"{prefix}{color}{text}{RESET}")

# ---------- 创建 Flask 应用 ----------
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

# ---------- Session 超时配置 ----------
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ---------- 授权中间件 ----------
@app.before_request
def check_license():
    whitelist = [
        '/', '/favicon.ico',
        '/api/v1/activate',
        '/api/v1/license/status',
        '/api/v1/license/activate-page',
        '/api/v1/license/upgrade-page',
        '/api/v1/license/quota-page',
        '/static/', '/css/', '/js/',
        '/api/v1/auth/login', '/api/v1/auth/register', '/api/v1/auth/logout',
        '/admin/login', '/admin/static/'
    ]
    for pattern in whitelist:
        if request.path == pattern or request.path.startswith(pattern):
            return None

    license_info = LicenseManager.verify_license()
    if not license_info['valid']:
        if request.path.startswith('/api/'):
            return jsonify({
                'code': 403,
                'message': license_info['message'],
                'data': {'activate_url': '/api/v1/license/activate-page'}
            }), 403
        return redirect('/api/v1/license/activate-page')

    if license_info['license_type'] == 'free' and request.method == 'POST':
        if request.path == '/api/v1/apps/import' or request.path.startswith('/api/v1/apps/batch'):
            can_add, msg = LicenseManager.can_add_app()
            if not can_add:
                return jsonify({
                    'code': 403,
                    'message': msg,
                    'data': {'upgrade_url': '/api/v1/license/upgrade-page'}
                }), 403
    return None

# ---------- 强制首次修改默认密码 ----------
@app.before_request
def enforce_password_change():
    if not request.path.startswith('/admin'):
        return None
    if request.path in ('/admin/login', '/admin/change-password', '/admin/static/'):
        return None

    users = load_users()
    admin_user = users.get('admin')
    if not admin_user:
        return None

    if check_password_hash(admin_user['password_hash'], 'admin123'):
        if not admin_user.get('password_changed', False):
            return redirect('/admin/change-password?first=1')
    return None

# ---------- 注册蓝图 ----------
register_blueprints(app)

# ---------- 日志轮转 ----------
try:
    from logging.handlers import RotatingFileHandler
    import logging
    from config import LOG_PATH
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=10*1024*1024, backupCount=5)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('应用启动，日志轮转已启用')
except Exception as e:
    print(f"[警告] 日志轮转配置失败: {e}")

# ---------- 启动入口 ----------
if __name__ == '__main__':
    local_ip = get_local_ip()
    apps = scan_apps()
    app_count = len(apps)
    enabled_count = sum(1 for a in apps if a.get('enabled', True))
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("\n" + "=" * 60)
    cprint("  🌟 万能应用加载器  v2.1.0", CYAN, bold=True)
    print("=" * 60)
    print(f"  🕒 启动时间: {start_time}")
    print(f"  📦 应用总数: {app_count} 个（已启用 {enabled_count} 个）")
    print(f"  🌐 本机 IP  : {GREEN}{local_ip}{RESET}")
    print(f"  🖥️  本地访问: {CYAN}http://127.0.0.1:{DEFAULT_PORT}{RESET}")
    if local_ip != '127.0.0.1':
        print(f"  📱 局域网访问: {CYAN}http://{local_ip}:{DEFAULT_PORT}{RESET}")

    license_info = LicenseManager.verify_license()
    if license_info['valid']:
        print(f"  🔑 授权状态: {GREEN}{license_info['license_type'].upper()}{RESET}")
        if license_info['license_type'] == 'free':
            quota = LicenseManager.get_quota_info()
            print(f"  📊 应用配额: {quota['used_apps']} / {quota['max_apps']}")
    else:
        print(f"  🔑 授权状态: {RED}未激活{RESET}")

    print("=" * 60)
    print("  💡 按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")

    try:
        webbrowser.open(f"http://127.0.0.1:{DEFAULT_PORT}", new=2)
    except:
        pass

    try:
        from livereload import Server
        server = Server(app.wsgi_app)
        print(f"🚀 启动 livereload 服务器，监听 http://0.0.0.0:{DEFAULT_PORT}\n")
        server.serve(host='0.0.0.0', port=DEFAULT_PORT, restart_delay=1)
    except ImportError:
        print(f"🚀 启动标准 Flask 服务器，监听 http://0.0.0.0:{DEFAULT_PORT}\n")
        app.run(host='0.0.0.0', port=DEFAULT_PORT, debug=True)