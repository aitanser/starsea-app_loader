#!/usr/bin/env python3
# __init__.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint

def register_blueprints(app):
    from .main import main_bp
    from .admin import admin_bp
    from .api.v1 import api_v1_bp
    from .api.v1.activate import activate_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    app.register_blueprint(activate_bp)