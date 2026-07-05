from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import load_users, save_users, create_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    if len(password) < 4:
        return jsonify({'error': '密码至少4位'}), 400
    users = load_users()
    if username in users:
        return jsonify({'error': '用户名已存在'}), 409
    if create_user(username, generate_password_hash(password), 'user'):
        session['user'] = username
        session['role'] = 'user'
        return jsonify({'status': 'ok', 'username': username, 'role': 'user'})
    return jsonify({'error': '注册失败'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    users = load_users()
    if username not in users:
        return jsonify({'error': '用户不存在'}), 404
    if not check_password_hash(users[username]['password_hash'], password):
        return jsonify({'error': '密码错误'}), 401
    session['user'] = username
    session['role'] = users[username].get('role', 'user')
    return jsonify({'status': 'ok', 'username': username, 'role': session['role']})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return jsonify({'status': 'ok'})

@auth_bp.route('/me', methods=['GET'])
def me():
    user = session.get('user')
    if not user:
        return jsonify({'error': '未登录'}), 401
    users = load_users()
    info = users.get(user, {})
    return jsonify({
        'username': user,
        'role': info.get('role', 'user'),
        'created': info.get('created')
    })