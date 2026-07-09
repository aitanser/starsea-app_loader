#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# activate.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, request, jsonify, render_template, redirect
from license import ActivationCodeManager, LicenseManager

activate_bp = Blueprint('activate', __name__, url_prefix='/api/v1')

@activate_bp.route('/activate', methods=['POST'])
def activate():
    data = request.json or {}
    code = data.get('activation_code', '').strip()
    if not code:
        return jsonify({'code': 400, 'message': '请输入激活码', 'data': None}), 400

    result = ActivationCodeManager.verify_code(code)
    if not result['valid']:
        return jsonify({'code': 400, 'message': result['message'], 'data': None}), 400

    license_info = result['license_info']
    if not ActivationCodeManager.save_license(license_info):
        return jsonify({'code': 500, 'message': '授权文件保存失败，请检查目录权限', 'data': None}), 500

    return jsonify({
        'code': 0,
        'message': '激活成功',
        'data': {
            'license_type': license_info.get('license_type'),
            'max_apps': license_info.get('max_apps'),
            'expires_at': license_info.get('expires_at')
        }
    })

@activate_bp.route('/license/status', methods=['GET'])
def get_license_status():
    info = LicenseManager.get_quota_info()
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': info
    })

@activate_bp.route('/license/activate-page', methods=['GET'])
def activate_page():
    license_info = LicenseManager.verify_license()
    if license_info['valid']:
        return redirect('/')
    return render_template('activate.html')

@activate_bp.route('/license/upgrade-page', methods=['GET'])
def upgrade_page():
    return render_template('upgrade.html')

@activate_bp.route('/license/quota-page', methods=['GET'])
def quota_page():
    return render_template('quota.html')