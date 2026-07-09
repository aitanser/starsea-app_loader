#!/usr/bin/env python3
# rating.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, request, jsonify
from models import load_apps_config, save_apps_config
import json
import os
from datetime import datetime
from config import DATA_DIR

rating_bp = Blueprint('rating', __name__)
RATING_PATH = os.path.join(DATA_DIR, 'ratings.json')

def load_ratings():
    if os.path.exists(RATING_PATH):
        with open(RATING_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_ratings(ratings):
    with open(RATING_PATH, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)

@rating_bp.route('/<app_id>', methods=['GET'])
def get_rating(app_id):
    ratings = load_ratings()
    app_rating = ratings.get(app_id, {'total': 0, 'count': 0, 'users': {}})
    avg = app_rating['total'] / app_rating['count'] if app_rating['count'] > 0 else 0
    return jsonify({
        'app_id': app_id,
        'average': round(avg, 1),
        'count': app_rating['count'],
        'distribution': {
            '1': sum(1 for u in app_rating.get('users', {}).values() if u == 1),
            '2': sum(1 for u in app_rating.get('users', {}).values() if u == 2),
            '3': sum(1 for u in app_rating.get('users', {}).values() if u == 3),
            '4': sum(1 for u in app_rating.get('users', {}).values() if u == 4),
            '5': sum(1 for u in app_rating.get('users', {}).values() if u == 5)
        }
    })

@rating_bp.route('/<app_id>', methods=['POST'])
def set_rating(app_id):
    data = request.json
    score = data.get('score')
    user = data.get('user', 'anonymous')

    if not score or score not in range(1, 6):
        return jsonify({'error': '评分必须是 1-5 的整数'}), 400

    ratings = load_ratings()
    if app_id not in ratings:
        ratings[app_id] = {'total': 0, 'count': 0, 'users': {}}

    if user in ratings[app_id]['users']:
        old_score = ratings[app_id]['users'][user]
        ratings[app_id]['total'] -= old_score
        ratings[app_id]['count'] -= 1

    ratings[app_id]['total'] += score
    ratings[app_id]['count'] += 1
    ratings[app_id]['users'][user] = score
    ratings[app_id]['last_updated'] = datetime.now().isoformat()

    save_ratings(ratings)
    return jsonify({'status': 'ok', 'average': round(ratings[app_id]['total'] / ratings[app_id]['count'], 1)})