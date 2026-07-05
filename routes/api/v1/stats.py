from flask import Blueprint, jsonify
from utils import get_trend_data

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/trend')
def trend():
    dates, values = get_trend_data(30)
    return jsonify({'dates': dates, 'values': values})