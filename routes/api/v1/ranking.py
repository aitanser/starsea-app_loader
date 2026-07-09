#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ranking.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
排行榜 API（增加文件缓存支持）
"""
from flask import Blueprint, jsonify, request
from models import scan_apps
from .rating import load_ratings
import time
import os
import json
from config import DATA_DIR

ranking_bp = Blueprint('ranking', __name__)

CACHE_DIR = os.path.join(DATA_DIR, 'cache', 'ranking')
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_TTL = 300  # 5 分钟


def get_cache(key: str):
    cache_path = os.path.join(CACHE_DIR, f'{key}.json')
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


def set_cache(key: str, data):
    cache_path = os.path.join(CACHE_DIR, f'{key}.json')
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({'timestamp': time.time(), 'data': data}, f, ensure_ascii=False)
    except:
        pass


@ranking_bp.route('/top/access')
def top_access():
    """按访问量排序（缓存 5 分钟）"""
    cached = get_cache('access')
    if cached is not None:
        return jsonify(cached)
    
    apps = scan_apps()
    sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
    result = sorted_apps[:20]
    set_cache('access', result)
    return jsonify(result)


@ranking_bp.route('/top/rating')
def top_rating():
    """按评分排序（缓存 5 分钟）"""
    cached = get_cache('rating')
    if cached is not None:
        return jsonify(cached)
    
    apps = scan_apps()
    ratings = load_ratings()
    for app in apps:
        r = ratings.get(app['id'], {'total': 0, 'count': 0})
        app['avg_rating'] = round(r['total'] / r['count'], 1) if r['count'] > 0 else 0
        app['rating_count'] = r['count']
    sorted_apps = sorted(apps, key=lambda x: x.get('avg_rating', 0), reverse=True)
    result = sorted_apps[:20]
    set_cache('rating', result)
    return jsonify(result)


@ranking_bp.route('/top/recent')
def top_recent():
    """按最后访问时间排序（缓存 2 分钟）"""
    cached = get_cache('recent')
    if cached is not None:
        return jsonify(cached)
    
    apps = scan_apps()
    sorted_apps = sorted(
        [a for a in apps if a.get('last_accessed')],
        key=lambda x: x.get('last_accessed', ''),
        reverse=True
    )
    result = sorted_apps[:20]
    set_cache('recent', result)
    return jsonify(result)


@ranking_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """清除排行榜缓存"""
    for f in os.listdir(CACHE_DIR):
        if f.endswith('.json'):
            try:
                os.remove(os.path.join(CACHE_DIR, f))
            except:
                pass
    return jsonify({'status': 'ok', 'message': '缓存已清除'})