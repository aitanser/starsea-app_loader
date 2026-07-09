#!/usr/bin/env python3
# stats.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, jsonify
from utils import get_trend_data

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/trend')
def trend():
    dates, values = get_trend_data(30)
    return jsonify({'dates': dates, 'values': values})