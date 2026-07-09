#!/usr/bin/env python3
# versions.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, request, jsonify, send_file
import os
import shutil
import zipfile
from datetime import datetime
from config import DATA_DIR, DEFAULT_APPS_DIR

versions_bp = Blueprint('versions', __name__)
BACKUP_DIR = os.path.join(DATA_DIR, 'backups', 'apps')
os.makedirs(BACKUP_DIR, exist_ok=True)

@versions_bp.route('/<app_id>')
def list_versions(app_id):
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith(app_id) and f.endswith('.zip'):
            parts = f.replace('.zip', '').split('_')
            if len(parts) >= 2:
                timestamp = parts[-1]
                backups.append({
                    'filename': f,
                    'timestamp': timestamp,
                    'path': os.path.join(BACKUP_DIR, f),
                    'size': os.path.getsize(os.path.join(BACKUP_DIR, f))
                })
    return jsonify(sorted(backups, key=lambda x: x['timestamp'], reverse=True))

@versions_bp.route('/<app_id>/backup', methods=['POST'])
def create_backup(app_id):
    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    if not os.path.exists(app_dir):
        return jsonify({'error': '应用不存在'}), 404

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'{app_id}_{timestamp}.zip'
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(app_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, app_dir)
                zf.write(file_path, arcname)

    return jsonify({
        'status': 'ok',
        'filename': backup_name,
        'timestamp': timestamp,
        'size': os.path.getsize(backup_path)
    })

@versions_bp.route('/<app_id>/rollback', methods=['POST'])
def rollback_version(app_id):
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': '需要 filename 参数'}), 400

    backup_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(backup_path):
        return jsonify({'error': '备份文件不存在'}), 404

    app_dir = os.path.join(DEFAULT_APPS_DIR, app_id)
    create_backup(app_id)

    for item in os.listdir(app_dir):
        item_path = os.path.join(app_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

    with zipfile.ZipFile(backup_path, 'r') as zf:
        zf.extractall(app_dir)

    return jsonify({'status': 'ok', 'message': f'已回滚到 {filename}'})