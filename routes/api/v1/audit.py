#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# audit.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
审计日志（SQLite 存储，支持轮转和查询）
"""
from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
from config import DATA_DIR

audit_bp = Blueprint('audit', __name__)
AUDIT_DB = os.path.join(DATA_DIR, 'audit.db')
MAX_RECORDS = 10000


def get_db():
    conn = sqlite3.connect(AUDIT_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user TEXT NOT NULL,
            action TEXT NOT NULL,
            app_id TEXT,
            details TEXT,
            ip TEXT,
            user_agent TEXT
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_user ON audit_log(user)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_action ON audit_log(action)')
    conn.commit()
    conn.close()


def prune_old_records():
    conn = get_db()
    conn.execute('''
        DELETE FROM audit_log 
        WHERE id NOT IN (
            SELECT id FROM audit_log ORDER BY id DESC LIMIT ?
        )
    ''', (MAX_RECORDS,))
    conn.commit()
    conn.close()


def save_audit_entry(entry: dict):
    conn = get_db()
    conn.execute('''
        INSERT INTO audit_log (timestamp, user, action, app_id, details, ip, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry.get('timestamp', datetime.now().isoformat()),
        entry.get('user', 'unknown'),
        entry.get('action', 'unknown'),
        entry.get('app_id'),
        entry.get('details', ''),
        entry.get('ip', ''),
        entry.get('user_agent', '')
    ))
    conn.commit()
    conn.close()
    total = conn.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
    if total > MAX_RECORDS:
        prune_old_records()


@audit_bp.route('', methods=['GET'])
def get_audit():
    limit = int(request.args.get('limit', 100))
    limit = min(limit, 500)
    offset = int(request.args.get('offset', 0))
    user = request.args.get('user', '')
    action = request.args.get('action', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    conn = get_db()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    if user:
        query += " AND user = ?"
        params.append(user)
    if action:
        query += " AND action = ?"
        params.append(action)
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@audit_bp.route('', methods=['POST'])
def log_audit():
    data = request.json or {}
    entry = {
        'timestamp': datetime.now().isoformat(),
        'user': data.get('user', 'admin'),
        'action': data.get('action', 'unknown'),
        'app_id': data.get('app_id'),
        'details': data.get('details', ''),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')
    }
    save_audit_entry(entry)
    return jsonify({'status': 'ok'})


@audit_bp.route('/stats', methods=['GET'])
def get_audit_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = conn.execute(
        'SELECT COUNT(*) FROM audit_log WHERE timestamp LIKE ?', 
        (today + '%',)
    ).fetchone()[0]
    action_stats = conn.execute('''
        SELECT action, COUNT(*) as count 
        FROM audit_log 
        GROUP BY action 
        ORDER BY count DESC 
        LIMIT 10
    ''').fetchall()
    conn.close()
    return jsonify({
        'total': total,
        'today': today_count,
        'actions': [{'action': row['action'], 'count': row['count']} for row in action_stats]
    })


init_db()