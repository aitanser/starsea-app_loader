from flask import Blueprint, jsonify, request
from models import scan_apps
from utils import load_user_history

recommend_bp = Blueprint('recommend', __name__)

def get_user_history(user):
    """从用户历史文件中获取访问过的应用 ID 列表"""
    history = load_user_history()
    return history.get(user, [])

@recommend_bp.route('/for/<user>')
def recommend_for_user(user):
    """为用户推荐应用，若无匹配则返回热门应用"""
    apps = scan_apps()
    history = get_user_history(user)

    # 无历史 → 热门
    if not history:
        sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
        return jsonify(sorted_apps[:10])

    # 收集用户访问过的应用的标签
    user_tags = set()
    for app in apps:
        if app['id'] in history:
            user_tags.update(app.get('tags', []))

    # 若用户访问的应用全部无标签 → 热门
    if not user_tags:
        sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
        return jsonify(sorted_apps[:10])

    # 基于标签相似度推荐（排除已访问的）
    candidates = []
    for app in apps:
        if app['id'] in history:
            continue
        app_tags = set(app.get('tags', []))
        match_count = len(user_tags.intersection(app_tags))
        if match_count > 0:
            candidates.append({
                **app,
                'match_score': match_count
            })

    # 无匹配 → 热门
    if not candidates:
        sorted_apps = sorted(apps, key=lambda x: x.get('access_count', 0), reverse=True)
        return jsonify(sorted_apps[:10])

    candidates.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(candidates[:10])