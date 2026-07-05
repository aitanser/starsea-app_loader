from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
from config import DATA_DIR

audit_bp = Blueprint('audit', __name__)
AUDIT_PATH = os.path.join(DATA_DIR, 'audit.json')

def load_audit():
    if os.path.exists(AUDIT_PATH):
        with open(AUDIT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_audit_entry(entry):
    audits = load_audit()
    audits.append(entry)
    if len(audits) > 1000:
        audits = audits[-500:]  # 保留最近 500 条
    with open(AUDIT_PATH, 'w', encoding='utf-8') as f:
        json.dump(audits, f, ensure_ascii=False, indent=2)

@audit_bp.route('', methods=['GET'])
def get_audit():
    """获取审计日志"""
    limit = int(request.args.get('limit', 100))
    audits = load_audit()
    return jsonify(audits[-limit:])

@audit_bp.route('', methods=['POST'])
def log_audit():
    """记录审计条目（内部调用）"""
    data = request.json
    entry = {
        'timestamp': datetime.now().isoformat(),
        'user': data.get('user', 'admin'),
        'action': data.get('action', 'unknown'),
        'app_id': data.get('app_id'),
        'details': data.get('details', {}),
        'ip': request.remote_addr
    }
    save_audit_entry(entry)
    return jsonify({'status': 'ok'})
