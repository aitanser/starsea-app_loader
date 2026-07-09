#!/usr/bin/env python3
# __init__.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint
from .apps import apps_bp
from .stats import stats_bp
from .system import system_bp
from .favorite import favorite_bp
from .note import note_bp
from .rating import rating_bp
from .ranking import ranking_bp
from .search import search_bp
from .screenshot import screenshot_bp
from .import_batch import import_batch_bp
from .audit import audit_bp
from .health import health_bp
from .tags import tags_bp
from .versions import versions_bp
from .recommend import recommend_bp
from .performance import performance_bp
from .auth import auth_bp

api_v1_bp = Blueprint('api_v1', __name__)
api_v1_bp.register_blueprint(apps_bp, url_prefix='/apps')
api_v1_bp.register_blueprint(stats_bp, url_prefix='/stats')
api_v1_bp.register_blueprint(system_bp, url_prefix='/system')
api_v1_bp.register_blueprint(favorite_bp, url_prefix='/favorite')
api_v1_bp.register_blueprint(note_bp, url_prefix='/note')
api_v1_bp.register_blueprint(rating_bp, url_prefix='/rating')
api_v1_bp.register_blueprint(ranking_bp, url_prefix='/ranking')
api_v1_bp.register_blueprint(search_bp, url_prefix='/search')
api_v1_bp.register_blueprint(screenshot_bp, url_prefix='/screenshot')
api_v1_bp.register_blueprint(import_batch_bp, url_prefix='/import')
api_v1_bp.register_blueprint(audit_bp, url_prefix='/audit')
api_v1_bp.register_blueprint(health_bp, url_prefix='/health')
api_v1_bp.register_blueprint(tags_bp, url_prefix='/tags')
api_v1_bp.register_blueprint(versions_bp, url_prefix='/versions')
api_v1_bp.register_blueprint(recommend_bp, url_prefix='/recommend')
api_v1_bp.register_blueprint(performance_bp, url_prefix='/performance')
api_v1_bp.register_blueprint(auth_bp, url_prefix='/auth')