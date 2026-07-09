#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# system.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
系统管理 API（增强版：备份一致性 + 恢复前备份）
"""
from flask import Blueprint, jsonify, request, send_file
from models import scan_apps
from utils import get_access_logs, safe_extract_zip
import os
import io
import zipfile
import shutil
import json
import threading
import time
from datetime import datetime
from config import DATA_DIR, LOG_PATH, DEFAULT_APPS_DIR

system_bp = Blueprint('system', __name__)

_backup_lock = threading.Lock()


@system_bp.route('/health')
def health():
    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
    except:
        cpu = mem = disk = 0
    
    apps = scan_apps()
    return jsonify({
        'cpu': cpu,
        'memory': mem,
        'disk': disk,
        'app_count': len(apps),
        'enabled_count': sum(1 for a in apps if a.get('enabled', True)),
        'log_size': os.path.getsize(LOG_PATH) if os.path.exists(LOG_PATH) else 0,
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/backup', methods=['POST'])
def backup():
    with _backup_lock:
        memory_file = io.BytesIO()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(DATA_DIR):
                if 'logs' in root or 'backups' in root:
                    continue
                for file in files:
                    if file.endswith('.tmp') or file.endswith('.lock'):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, DATA_DIR)
                    zf.write(file_path, arcname)
        memory_file.seek(0)
        return send_file(
            memory_file,
            download_name=f'backup_{timestamp}.zip',
            as_attachment=True,
            mimetype='application/zip'
        )


@system_bp.route('/restore', methods=['POST'])
def restore():
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        return jsonify({'error': '请上传 zip 文件'}), 400
    
    # 恢复前自动备份
    backup_dir = os.path.join(DATA_DIR, 'backups', 'pre_restore')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'pre_restore_{timestamp}.zip')
    
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(DATA_DIR):
                if 'logs' in root or 'backups' in root:
                    continue
                for f in files:
                    if f.endswith('.tmp') or f.endswith('.lock'):
                        continue
                    file_path = os.path.join(root, f)
                    arcname = os.path.relpath(file_path, DATA_DIR)
                    zf.write(file_path, arcname)
    except Exception as e:
        pass
    
    try:
        safe_extract_zip(file, DATA_DIR)
        return jsonify({
            'status': 'ok',
            'message': '恢复成功，已自动创建恢复前备份',
            'backup_path': backup_path if os.path.exists(backup_path) else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@system_bp.route('/backup/list', methods=['GET'])
def list_backups():
    backup_dir = os.path.join(DATA_DIR, 'backups')
    if not os.path.exists(backup_dir):
        return jsonify([])
    backups = []
    for root, dirs, files in os.walk(backup_dir):
        for f in files:
            if f.endswith('.zip'):
                file_path = os.path.join(root, f)
                rel_path = os.path.relpath(file_path, backup_dir)
                backups.append({
                    'name': f,
                    'path': rel_path,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
    backups.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify(backups)


@system_bp.route('/backup/clean', methods=['POST'])
def clean_old_backups():
    backup_dir = os.path.join(DATA_DIR, 'backups')
    if not os.path.exists(backup_dir):
        return jsonify({'status': 'ok', 'removed': 0})
    cutoff = time.time() - 30 * 24 * 3600
    removed = 0
    for root, dirs, files in os.walk(backup_dir):
        for f in files:
            if f.endswith('.zip'):
                file_path = os.path.join(root, f)
                if os.path.getmtime(file_path) < cutoff:
                    try:
                        os.remove(file_path)
                        removed += 1
                    except:
                        pass
    return jsonify({'status': 'ok', 'removed': removed, 'message': f'已清理 {removed} 个过期备份'})