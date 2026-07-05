#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import webbrowser
from datetime import datetime
from flask import Flask
from config import DEFAULT_PORT
from routes import register_blueprints
from utils import get_local_ip
from models import scan_apps

# ---------- 颜色辅助（兼容 Windows） ----------
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
    # ---- 获取启动信息 ----
    local_ip = get_local_ip()
    apps = scan_apps()
    app_count = len(apps)
    enabled_count = sum(1 for a in apps if a.get('enabled', True))
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # ---- 清屏（可选） ----
    # os.system('cls' if os.name == 'nt' else 'clear')

    # ---- 打印横幅 ----
    print("\n" + "=" * 60)
    cprint("  🌟 万能应用加载器  v2.0", CYAN, bold=True)
    print("=" * 60)
    print(f"  🕒 启动时间: {start_time}")
    print(f"  📦 应用总数: {app_count} 个（已启用 {enabled_count} 个）")
    print(f"  🌐 本机 IP  : {GREEN}{local_ip}{RESET}")
    print(f"  🖥️  本地访问: {CYAN}http://127.0.0.1:{DEFAULT_PORT}{RESET}")
    if local_ip != '127.0.0.1':
        print(f"  📱 局域网访问: {CYAN}http://{local_ip}:{DEFAULT_PORT}{RESET}")
    print("=" * 60)
    print("  💡 按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")

    # ---- 自动打开浏览器 ----
    try:
        webbrowser.open(f"http://127.0.0.1:{DEFAULT_PORT}", new=2)
    except:
        pass

    # ---- 启动服务器 ----
    try:
        from livereload import Server
        server = Server(app.wsgi_app)
        print(f"🚀 启动 livereload 服务器，监听 http://0.0.0.0:{DEFAULT_PORT}\n")
        server.serve(host='0.0.0.0', port=DEFAULT_PORT, restart_delay=1)
    except ImportError:
        print(f"🚀 启动标准 Flask 服务器，监听 http://0.0.0.0:{DEFAULT_PORT}\n")
        app.run(host='0.0.0.0', port=DEFAULT_PORT, debug=True)