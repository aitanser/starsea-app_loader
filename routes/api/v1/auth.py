#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# auth.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
用户认证 API（含登录失败限制）
"""
from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import load_users, save_users, create_user
import time
import os
import json
from config import DATA_DIR

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 登录失败限制配置
LOGIN_FAIL_FILE = os.path.join(DATA_DIR, 'login_fails.json')
MAX_FAIL_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 分钟


def load_fail_records() -> dict:
    """加载登录失败记录"""
    if not os.path.exists(LOGIN_FAIL_FILE):
        return {}
    try:
        with open(LOGIN_FAIL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def save_fail_records(records: dict) -> None:
    """保存登录失败记录"""
    os.makedirs(os.path.dirname(LOGIN_FAIL_FILE), exist_ok=True)
    current_time = time.time()
    cleaned = {k: v for k, v in records.items() 
               if current_time - v.get('last_fail', 0) < LOCKOUT_DURATION}
    with open(LOGIN_FAIL_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)


def is_ip_locked(ip: str):
    """检查 IP 是否被锁定，返回 (是否锁定, 剩余秒数)"""
    records = load_fail_records()
    if ip not in records:
        return False, 0
    
    record = records[ip]
    if record.get('count', 0) >= MAX_FAIL_ATTEMPTS:
        elapsed = time.time() - record.get('last_fail', 0)
        if elapsed < LOCKOUT_DURATION:
            return True, int(LOCKOUT_DURATION - elapsed)
        else:
            records[ip] = {'count': 0, 'last_fail': 0}
            save_fail_records(records)
            return False, 0
    
    return False, 0


def record_fail_attempt(ip: str) -> None:
    """记录一次失败尝试"""
    records = load_fail_records()
    if ip not in records:
        records[ip] = {'count': 0, 'last_fail': 0}
    records[ip]['count'] = records[ip].get('count', 0) + 1
    records[ip]['last_fail'] = time.time()
    save_fail_records(records)


def reset_fail_records(ip: str) -> None:
    """重置失败记录（登录成功后调用）"""
    records = load_fail_records()
    if ip in records:
        records[ip] = {'count': 0, 'last_fail': 0}
        save_fail_records(records)


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
        session.permanent = True
        session['user'] = username
        session['role'] = 'user'
        return jsonify({'status': 'ok', 'username': username, 'role': 'user'})
    
    return jsonify({'error': '注册失败'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    client_ip = request.remote_addr or 'unknown'
    
    locked, remaining = is_ip_locked(client_ip)
    if locked:
        return jsonify({
            'error': f'登录失败次数过多，请 {remaining} 秒后重试',
            'locked': True,
            'remaining': remaining
        }), 429
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    users = load_users()
    if username not in users:
        record_fail_attempt(client_ip)
        return jsonify({'error': '用户名或密码错误'}), 401
    
    if not check_password_hash(users[username]['password_hash'], password):
        record_fail_attempt(client_ip)
        return jsonify({'error': '用户名或密码错误'}), 401
    
    reset_fail_records(client_ip)
    session.permanent = True
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