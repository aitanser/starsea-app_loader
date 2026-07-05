from flask import Blueprint

def register_blueprints(app):
    from .main import main_bp
    from .admin import admin_bp
    from .api.v1 import api_v1_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')