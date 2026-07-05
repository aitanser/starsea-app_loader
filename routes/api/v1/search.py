from flask import Blueprint, request, jsonify
from models import scan_apps

search_bp = Blueprint('search', __name__)

@search_bp.route('')
def search_apps():
    """增强搜索：支持名称、描述、分类、标签、作者等"""
    keyword = request.args.get('q', '').lower().strip()
    fields = request.args.get('fields', 'name,description,category,tags').split(',')
    limit = int(request.args.get('limit', 50))

    if not keyword:
        return jsonify([])

    apps = scan_apps()
    results = []
    for app in apps:
        score = 0
        match_fields = []
        for field in fields:
            if field == 'name' and keyword in app.get('name', '').lower():
                score += 5
                match_fields.append('name')
            elif field == 'description' and keyword in app.get('description', '').lower():
                score += 3
                match_fields.append('description')
            elif field == 'category' and keyword in app.get('category', '').lower():
                score += 2
                match_fields.append('category')
            elif field == 'tags':
                for tag in app.get('tags', []):
                    if keyword in tag.lower():
                        score += 2
                        match_fields.append('tag:' + tag)
            elif field == 'author' and keyword in app.get('author', '').lower():
                score += 4
                match_fields.append('author')

        if score > 0:
            app_copy = app.copy()
            app_copy['match_score'] = score
            app_copy['match_fields'] = match_fields
            results.append(app_copy)

    # 按匹配度排序
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(results[:limit])
