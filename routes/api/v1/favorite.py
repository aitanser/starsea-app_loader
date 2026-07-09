#!/usr/bin/env python3
# favorite.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, request, jsonify
from models import load_favorites, save_favorites

favorite_bp = Blueprint('favorite', __name__)

@favorite_bp.route('/<app_id>', methods=['POST'])
def toggle_favorite(app_id):
    data = request.json
    favorite = data.get('favorite', True)
    favorites = load_favorites()
    if favorite:
        if app_id not in favorites:
            favorites.append(app_id)
    else:
        if app_id in favorites:
            favorites.remove(app_id)
    save_favorites(favorites)
    return jsonify({'status': 'ok', 'favorite': favorite})