#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# health.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
健康检查 API（增强版：自动定时检查 + HTTP 实际访问验证）
"""
from flask import Blueprint, jsonify, request
from models import scan_apps
from datetime import datetime
import json
import os
import threading
import time
import requests
from config import DATA_DIR, DEFAULT_APPS_DIR

health_bp = Blueprint('health', __name__)
HEALTH_PATH = os.path.join(DATA_DIR, 'health.json')
AUTO_CHECK_INTERVAL = 3600  # 1 小时
BASE_URL = os.environ.get('LOADER_BASE_URL', 'http://127.0.0.1:8000')


def load_health_data():
    if os.path.exists(HEALTH_PATH):
        try:
            with open(HEALTH_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_health_data(data):
    with open(HEALTH_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_app_health(app_id: str, entry: str = 'index.html') -> dict:
    """检查应用健康状态（文件 + HTTP）"""
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    if not os.path.exists(app_dir):
        return {'status': 'error', 'message': '应用目录不存在'}

    entry_path = os.path.join(app_dir, entry)
    if not os.path.exists(entry_path):
        return {'status': 'unhealthy', 'message': f'入口文件 {entry} 不存在'}

    try:
        url = f"{BASE_URL}/app/{app_id}/{entry}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return {'status': 'healthy', 'message': 'HTTP 200 OK'}
        else:
            return {'status': 'unhealthy', 'message': f'HTTP {resp.status_code}'}
    except requests.exceptions.Timeout:
        return {'status': 'unhealthy', 'message': 'HTTP 超时'}
    except requests.exceptions.ConnectionError:
        return {'status': 'unhealthy', 'message': '连接失败'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': str(e)}


def auto_check_health():
    """自动健康检查（后台线程）"""
    while True:
        try:
            apps = scan_apps()
            data = load_health_data()
            for app in apps:
                result = check_app_health(app['id'], app.get('entry', 'index.html'))
                data[app['id']] = {
                    **result,
                    'last_check': datetime.now().isoformat(),
                    'app_name': app['name']
                }
            save_health_data(data)
        except Exception as e:
            print(f"[健康检查] 自动检查失败: {e}")
        time.sleep(AUTO_CHECK_INTERVAL)


_health_thread_started = False


def start_health_thread():
    global _health_thread_started
    if not _health_thread_started:
        _health_thread_started = True
        thread = threading.Thread(target=auto_check_health, daemon=True)
        thread.start()


threading.Timer(10, start_health_thread).start()


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
        'healthy': sum(1 for r in results.values() if r.get('status') == 'healthy'),
        'unhealthy': sum(1 for r in results.values() if r.get('status') == 'unhealthy'),
        'error': sum(1 for r in results.values() if r.get('status') == 'error'),
        'disabled': sum(1 for r in results.values() if r.get('status') == 'disabled'),
        'details': results
    })


@health_bp.route('/status')
def health_status():
    data = load_health_data()
    apps = scan_apps()
    
    for app in apps:
        if app['id'] not in data:
            data[app['id']] = {
                'status': 'unknown',
                'message': '尚未检查',
                'app_name': app['name']
            }
        else:
            data[app['id']]['app_name'] = app['name']
    save_health_data(data)
    
    return jsonify({
        'total': len(data),
        'healthy': sum(1 for r in data.values() if r.get('status') == 'healthy'),
        'unhealthy': sum(1 for r in data.values() if r.get('status') == 'unhealthy'),
        'error': sum(1 for r in data.values() if r.get('status') == 'error'),
        'disabled': sum(1 for r in data.values() if r.get('status') == 'disabled'),
        'unknown': sum(1 for r in data.values() if r.get('status') == 'unknown'),
        'details': data
    })