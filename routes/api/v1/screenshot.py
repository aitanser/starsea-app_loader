#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# screenshot.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
截图服务（增加队列和缓存清理）
"""
from flask import Blueprint, request, jsonify, send_file
import os
import hashlib
import threading
import time
from datetime import datetime, timedelta
from config import DEFAULT_APPS_DIR, DATA_DIR

screenshot_bp = Blueprint('screenshot', __name__)

SCREENSHOT_DIR = os.path.join(DATA_DIR, 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

_screenshot_queue = []
_QUEUE_LOCK = threading.Lock()
_QUEUE_WORKER_RUNNING = False


def get_app_entry(app_id):
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
                entry = config.get('fallback') or config.get('entry', 'index.html')
        except:
            pass

    if os.path.exists(os.path.join(app_dir, entry)):
        return entry
    for f in os.listdir(app_dir):
        if f.endswith('.html'):
            return f
    return None


def clean_old_cache():
    """清理超过 7 天的截图缓存"""
    cutoff = time.time() - 7 * 24 * 3600
    for f in os.listdir(SCREENSHOT_DIR):
        path = os.path.join(SCREENSHOT_DIR, f)
        if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
            try:
                os.remove(path)
            except:
                pass


def generate_screenshot_async(app_id, entry, app_dir, screenshot_path):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return

    base_url = os.environ.get("LOADER_BASE_URL", "http://127.0.0.1:8000")
    app_url = f"{base_url}/app/{app_id}/{entry}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(app_url, wait_until='networkidle', timeout=15000)
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()
    except Exception:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)


def screenshot_worker():
    global _QUEUE_WORKER_RUNNING
    while _QUEUE_WORKER_RUNNING:
        task = None
        with _QUEUE_LOCK:
            if _screenshot_queue:
                task = _screenshot_queue.pop(0)
        
        if task:
            generate_screenshot_async(
                task['app_id'], 
                task['entry'], 
                task['app_dir'], 
                task['screenshot_path']
            )
        else:
            time.sleep(1)


def start_worker():
    global _QUEUE_WORKER_RUNNING
    if not _QUEUE_WORKER_RUNNING:
        _QUEUE_WORKER_RUNNING = True
        thread = threading.Thread(target=screenshot_worker, daemon=True)
        thread.start()


start_worker()


@screenshot_bp.route('/<app_id>')
def get_screenshot(app_id):
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    if not os.path.exists(app_dir):
        return jsonify({'error': '应用不存在'}), 404

    entry = get_app_entry(app_id)
    if not entry:
        return jsonify({'error': '未找到 HTML 入口文件'}), 404

    hash_key = hashlib.md5(f"{app_id}_{entry}".encode()).hexdigest()
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{hash_key}.png")

    if os.path.exists(screenshot_path):
        mtime = os.path.getmtime(screenshot_path)
        if (time.time() - mtime) < 3600:
            return send_file(screenshot_path, mimetype='image/png')

    with _QUEUE_LOCK:
        for task in _screenshot_queue:
            if task['app_id'] == app_id:
                break
        else:
            _screenshot_queue.append({
                'app_id': app_id,
                'entry': entry,
                'app_dir': app_dir,
                'screenshot_path': screenshot_path
            })

    try:
        from playwright.sync_api import sync_playwright
        generate_screenshot_async(app_id, entry, app_dir, screenshot_path)
        if os.path.exists(screenshot_path):
            return send_file(screenshot_path, mimetype='image/png')
    except ImportError:
        pass

    return jsonify({
        'status': 'pending',
        'message': '截图正在生成中，请稍后刷新'
    }), 202


@screenshot_bp.route('/cache/clean', methods=['POST'])
def clean_cache():
    clean_old_cache()
    return jsonify({'status': 'ok', 'message': '缓存已清理'})