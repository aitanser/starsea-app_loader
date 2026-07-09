#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# recommend.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
推荐系统 API（增强版 + 缓存）
"""
from flask import Blueprint, jsonify, request
from models import scan_apps
from utils import load_user_history
from .ranking import top_access
import time
import os
import json
from config import DATA_DIR

recommend_bp = Blueprint('recommend', __name__)

CACHE_DIR = os.path.join(DATA_DIR, 'cache', 'recommend')
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 600  # 10 分钟


def get_cache(user: str):
    cache_path = os.path.join(CACHE_DIR, f'{user}.json')
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if time.time() - data.get('timestamp', 0) > CACHE_TTL:
            return None
        return data.get('data')
    except:
        return None


def set_cache(user: str, data):
    cache_path = os.path.join(CACHE_DIR, f'{user}.json')
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({'timestamp': time.time(), 'data': data}, f, ensure_ascii=False)
    except:
        pass


def get_user_history(user):
    history = load_user_history()
    return history.get(user, [])


@recommend_bp.route('/for/<user>')
def recommend_for_user(user):
    """为用户推荐应用（缓存 10 分钟）"""
    if user == 'anonymous' or not user:
        return top_access()
    
    cached = get_cache(user)
    if cached is not None:
        return jsonify(cached)
    
    apps = scan_apps()
    history = get_user_history(user)
    
    if not history:
        sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
        result = sorted_apps[:10]
        set_cache(user, result)
        return jsonify(result)
    
    user_tags = set()
    for app in apps:
        if app['id'] in history:
            user_tags.update(app.get('tags', []))
    
    if not user_tags:
        sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
        result = sorted_apps[:10]
        set_cache(user, result)
        return jsonify(result)
    
    candidates = []
    for app in apps:
        if app['id'] in history:
            continue
        app_tags = set(app.get('tags', []))
        match_count = len(user_tags.intersection(app_tags))
        if match_count > 0:
            candidates.append({
                **app,
                'match_score': match_count,
                'match_tags': list(user_tags.intersection(app_tags))
            })
    
    if not candidates:
        sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
        result = sorted_apps[:10]
        set_cache(user, result)
        return jsonify(result)
    
    candidates.sort(key=lambda x: x['match_score'], reverse=True)
    result = candidates[:10]
    set_cache(user, result)
    return jsonify(result)


@recommend_bp.route('/cache/clear/<user>', methods=['POST'])
def clear_user_cache(user):
    cache_path = os.path.join(CACHE_DIR, f'{user}.json')
    if os.path.exists(cache_path):
        os.remove(cache_path)
    return jsonify({'status': 'ok', 'message': f'用户 {user} 的推荐缓存已清除'})


@recommend_bp.route('/cache/clear', methods=['POST'])
def clear_all_cache():
    for f in os.listdir(CACHE_DIR):
        if f.endswith('.json'):
            try:
                os.remove(os.path.join(CACHE_DIR, f))
            except:
                pass
    return jsonify({'status': 'ok', 'message': '所有推荐缓存已清除'})