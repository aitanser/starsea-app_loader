#!/usr/bin/env python3
# tags.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, jsonify, request
from models import scan_apps
import os
import json
from config import DEFAULT_APPS_DIR

tags_bp = Blueprint('tags', __name__)

def _read_app_json(app_id):
    app_json_path = os.path.join(DEFAULT_APPS_DIR, app_id, 'app.json')
    if not os.path.exists(app_json_path):
        return {}
    try:
        with open(app_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def _write_app_json(app_id, config):
    app_json_path = os.path.join(DEFAULT_APPS_DIR, app_id, 'app.json')
    os.makedirs(os.path.dirname(app_json_path), exist_ok=True)
    with open(app_json_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def _get_all_apps():
    return scan_apps()

@tags_bp.route('/', methods=['GET'])
def list_tags():
    apps = _get_all_apps()
    tag_count = {}
    for app in apps:
        for tag in app.get('tags', []):
            tag_count[tag] = tag_count.get(tag, 0) + 1
    sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
    return jsonify([{'name': t, 'count': c} for t, c in sorted_tags])

@tags_bp.route('/cloud', methods=['GET'])
def tag_cloud():
    apps = _get_all_apps()
    tag_count = {}
    for app in apps:
        for tag in app.get('tags', []):
            tag_count[tag] = tag_count.get(tag, 0) + 1
    max_count = max(tag_count.values()) if tag_count else 1
    result = []
    for tag, count in tag_count.items():
        app_names = [app['name'] for app in apps if tag in app.get('tags', [])]
        result.append({
            'name': tag,
            'count': count,
            'weight': round(count / max_count * 10, 1),
            'apps': app_names
        })
    result.sort(key=lambda x: x['count'], reverse=True)
    return jsonify(result)

@tags_bp.route('/rename', methods=['PUT'])
def rename_tag():
    data = request.json
    old_tag = data.get('old')
    new_tag = data.get('new')
    if not old_tag or not new_tag:
        return jsonify({'error': '缺少 old 或 new 参数'}), 400
    if old_tag == new_tag:
        return jsonify({'error': '新旧标签相同'}), 400

    apps = _get_all_apps()
    updated_count = 0
    for app in apps:
        app_id = app['id']
        config = _read_app_json(app_id)
        tags = config.get('tags', [])
        if old_tag in tags:
            new_tags = [new_tag if t == old_tag else t for t in tags]
            seen = set()
            unique_tags = []
            for t in new_tags:
                if t not in seen:
                    seen.add(t)
                    unique_tags.append(t)
            config['tags'] = unique_tags
            _write_app_json(app_id, config)
            updated_count += 1

    return jsonify({
        'status': 'ok',
        'message': f'标签 "{old_tag}" 已重命名为 "{new_tag}"，共更新 {updated_count} 个应用'
    })

@tags_bp.route('/<tag_name>', methods=['DELETE'])
def delete_tag(tag_name):
    apps = _get_all_apps()
    updated_count = 0
    for app in apps:
        app_id = app['id']
        config = _read_app_json(app_id)
        tags = config.get('tags', [])
        if tag_name in tags:
            config['tags'] = [t for t in tags if t != tag_name]
            _write_app_json(app_id, config)
            updated_count += 1

    return jsonify({
        'status': 'ok',
        'message': f'标签 "{tag_name}" 已从所有应用中移除，共更新 {updated_count} 个应用'
    })

@tags_bp.route('/merge', methods=['POST'])
def merge_tags():
    data = request.json
    source = data.get('source')
    target = data.get('target')
    if not source or not target:
        return jsonify({'error': '需要 source 和 target 参数'}), 400
    if source == target:
        return jsonify({'error': '源标签和目标标签相同'}), 400

    apps = _get_all_apps()
    updated_count = 0
    for app in apps:
        app_id = app['id']
        config = _read_app_json(app_id)
        tags = config.get('tags', [])
        if source in tags or target in tags:
            new_tags = [target if t == source else t for t in tags]
            seen = set()
            unique_tags = []
            for t in new_tags:
                if t not in seen:
                    seen.add(t)
                    unique_tags.append(t)
            config['tags'] = unique_tags
            _write_app_json(app_id, config)
            updated_count += 1

    return jsonify({
        'status': 'ok',
        'message': f'标签 "{source}" 已合并到 "{target}"，共更新 {updated_count} 个应用'
    })

@tags_bp.route('/<app_id>', methods=['GET'])
def get_app_tags(app_id):
    app = next((a for a in _get_all_apps() if a['id'] == app_id), None)
    if not app:
        return jsonify({'error': '应用不存在'}), 404
    return jsonify(app.get('tags', []))

@tags_bp.route('/<app_id>', methods=['POST'])
def add_app_tag(app_id):
    app = next((a for a in _get_all_apps() if a['id'] == app_id), None)
    if not app:
        return jsonify({'error': '应用不存在'}), 404

    data = request.json
    new_tag = data.get('tag')
    if not new_tag or not new_tag.strip():
        return jsonify({'error': '标签不能为空'}), 400
    new_tag = new_tag.strip()

    config = _read_app_json(app_id)
    tags = config.get('tags', [])
    if new_tag in tags:
        return jsonify({'error': '标签已存在'}), 409

    tags.append(new_tag)
    config['tags'] = tags
    _write_app_json(app_id, config)
    return jsonify({'status': 'ok', 'tags': tags})

@tags_bp.route('/<app_id>/<tag>', methods=['DELETE'])
def remove_app_tag(app_id, tag):
    app = next((a for a in _get_all_apps() if a['id'] == app_id), None)
    if not app:
        return jsonify({'error': '应用不存在'}), 404

    config = _read_app_json(app_id)
    tags = config.get('tags', [])
    if tag not in tags:
        return jsonify({'error': '标签不存在'}), 404

    new_tags = [t for t in tags if t != tag]
    config['tags'] = new_tags
    _write_app_json(app_id, config)
    return jsonify({'status': 'ok', 'tags': new_tags})