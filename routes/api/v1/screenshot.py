from flask import Blueprint, request, jsonify, send_file
import os
import hashlib
from datetime import datetime
from config import DEFAULT_APPS_DIR, DATA_DIR

screenshot_bp = Blueprint('screenshot', __name__)

SCREENSHOT_DIR = os.path.join(DATA_DIR, 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def get_app_entry(app_id):
    """获取应用的入口文件，优先 fallback（适配 SPA）"""
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    if not os.path.exists(app_dir):
        return None

    config_path = os.path.join(app_dir, 'app.json')
    entry = 'index.html'
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 优先使用 fallback（SPA），再 entry，最后默认 index.html
                entry = config.get('fallback') or config.get('entry', 'index.html')
        except:
            pass

    if os.path.exists(os.path.join(app_dir, entry)):
        return entry
    # 如果指定入口不存在，查找第一个 HTML
    for f in os.listdir(app_dir):
        if f.endswith('.html'):
            return f
    return None

@screenshot_bp.route('/<app_id>')
def get_screenshot(app_id):
    """获取应用截图（如果已缓存则直接返回，否则生成）"""
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    if not os.path.exists(app_dir):
        return jsonify({'error': '应用不存在'}), 404

    entry = get_app_entry(app_id)
    if not entry:
        return jsonify({'error': '未找到 HTML 入口文件'}), 404

    hash_key = hashlib.md5(f"{app_id}_{entry}".encode()).hexdigest()
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{hash_key}.png")

    # 检查缓存
    if os.path.exists(screenshot_path):
        mtime = os.path.getmtime(screenshot_path)
        if (datetime.now().timestamp() - mtime) < 3600:
            return send_file(screenshot_path, mimetype='image/png')

    # 尝试使用 playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # 返回 503 并提示安装
        return jsonify({
            'error': 'Playwright 未安装，请运行: pip install playwright && playwright install'
        }), 503

    base_url = request.host_url.rstrip('/')
    app_url = f"{base_url}/app/{app_id}/{entry}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(app_url, wait_until='networkidle', timeout=15000)
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()
        return send_file(screenshot_path, mimetype='image/png')
    except Exception as e:
        # 删除可能产生的损坏缓存文件
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        return jsonify({'error': f'截图生成失败: {str(e)}'}), 503