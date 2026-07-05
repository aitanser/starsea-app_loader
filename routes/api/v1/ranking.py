from flask import Blueprint, jsonify
from models import scan_apps
from .rating import load_ratings

ranking_bp = Blueprint('ranking', __name__)

@ranking_bp.route('/top/access')
def top_access():
    """按访问量排序"""
    apps = scan_apps()
    sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
    return jsonify(sorted_apps[:20])

@ranking_bp.route('/top/rating')
def top_rating():
    """按评分排序"""
    apps = scan_apps()
    ratings = load_ratings()
    for app in apps:
        r = ratings.get(app['id'], {'total': 0, 'count': 0})
        app['avg_rating'] = round(r['total'] / r['count'], 1) if r['count'] > 0 else 0
        app['rating_count'] = r['count']
    sorted_apps = sorted(apps, key=lambda x: x.get('avg_rating', 0), reverse=True)
    return jsonify(sorted_apps[:20])

@ranking_bp.route('/top/recent')
def top_recent():
    """按最后访问时间排序"""
    apps = scan_apps()
    sorted_apps = sorted(
        [a for a in apps if a.get('last_accessed')],
        key=lambda x: x.get('last_accessed', ''),
        reverse=True
    )
    return jsonify(sorted_apps[:20])
