#!/usr/bin/env python3
# import_batch.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, request, jsonify
import os
import zipfile
import shutil
from datetime import datetime
from config import DEFAULT_APPS_DIR
from utils import safe_extract_zip, has_html_files

import_batch_bp = Blueprint('import_batch', __name__)

@import_batch_bp.route('', methods=['POST'])
def import_batch():
    if 'files' not in request.files:
        return jsonify({'error': '未上传文件'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': '没有选择文件'}), 400

    results = []
    for file in files:
        if file.filename == '' or not file.filename.endswith('.zip'):
            results.append({'filename': file.filename, 'status': 'error', 'message': '不是 zip 文件'})
            continue

        try:
            app_name = os.path.splitext(file.filename)[0]
            target_path = os.path.join(DEFAULT_APPS_DIR, app_name)
            if os.path.exists(target_path):
                app_name = app_name + '_' + datetime.now().strftime('%Y%m%d%H%M%S')
                target_path = os.path.join(DEFAULT_APPS_DIR, app_name)

            safe_extract_zip(file, target_path)

            if not has_html_files(target_path):
                shutil.rmtree(target_path)
                results.append({'filename': file.filename, 'status': 'error', 'message': '未找到 HTML 文件'})
                continue

            if not os.path.exists(os.path.join(target_path, 'app.json')):
                import json
                with open(os.path.join(target_path, 'app.json'), 'w', encoding='utf-8') as f:
                    json.dump({'name': app_name, 'entry': 'index.html'}, f, ensure_ascii=False, indent=2)

            results.append({
                'filename': file.filename,
                'status': 'ok',
                'app_id': app_name,
                'message': '导入成功'
            })
        except Exception as e:
            results.append({'filename': file.filename, 'status': 'error', 'message': str(e)})

    return jsonify({'results': results, 'total': len(results), 'success': sum(1 for r in results if r['status'] == 'ok')})