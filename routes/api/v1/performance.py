#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# performance.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
性能监控 API（SQLite 存储）
"""
from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
from config import DATA_DIR

performance_bp = Blueprint('performance', __name__)
PERF_DB = os.path.join(DATA_DIR, 'performance.db')


def get_db():
    conn = sqlite3.connect(PERF_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            load_time REAL,
            resource_size INTEGER,
            request_count INTEGER,
            user_agent TEXT,
            ip TEXT
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_perf_app ON performance(app_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_perf_time ON performance(timestamp)')
    conn.commit()
    conn.close()


init_db()


@performance_bp.route('/<app_id>/report', methods=['POST'])
def report_performance(app_id):
    data = request.json or {}
    conn = get_db()
    conn.execute('''
        INSERT INTO performance (app_id, timestamp, load_time, resource_size, request_count, user_agent, ip)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        app_id,
        datetime.now().isoformat(),
        data.get('load_time', 0),
        data.get('resource_size', 0),
        data.get('request_count', 1),
        request.headers.get('User-Agent', ''),
        request.remote_addr or ''
    ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@performance_bp.route('/<app_id>')
def get_performance(app_id):
    days = int(request.args.get('days', 7))
    limit = int(request.args.get('limit', 100))
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    conn = get_db()
    rows = conn.execute('''
        SELECT * FROM performance 
        WHERE app_id = ? AND timestamp >= ?
        ORDER BY id DESC LIMIT ?
    ''', (app_id, cutoff, limit)).fetchall()
    stats = conn.execute('''
        SELECT 
            COUNT(*) as count,
            AVG(load_time) as avg_load_time,
            MAX(load_time) as max_load_time,
            MIN(load_time) as min_load_time,
            AVG(resource_size) as avg_resource_size,
            SUM(resource_size) as total_resource_size
        FROM performance 
        WHERE app_id = ? AND timestamp >= ? AND load_time > 0
    ''', (app_id, cutoff)).fetchone()
    daily = conn.execute('''
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as count,
            AVG(load_time) as avg_load
        FROM performance 
        WHERE app_id = ? AND timestamp >= ?
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    ''', (app_id, cutoff)).fetchall()
    conn.close()
    return jsonify({
        'app_id': app_id,
        'stats': {
            'count': stats['count'] if stats else 0,
            'avg_load_time': round(stats['avg_load_time'], 2) if stats and stats['avg_load_time'] else 0,
            'max_load_time': round(stats['max_load_time'], 2) if stats and stats['max_load_time'] else 0,
            'min_load_time': round(stats['min_load_time'], 2) if stats and stats['min_load_time'] else 0,
            'avg_resource_size': round(stats['avg_resource_size'] / 1024, 2) if stats and stats['avg_resource_size'] else 0,
            'total_resource_size': round(stats['total_resource_size'] / 1024, 2) if stats and stats['total_resource_size'] else 0
        },
        'daily_trend': [dict(row) for row in daily],
        'recent': [dict(row) for row in rows[:20]]
    })


@performance_bp.route('/dashboard')
def dashboard():
    days = int(request.args.get('days', 7))
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    conn = get_db()
    apps = conn.execute('''
        SELECT 
            app_id,
            COUNT(*) as count,
            AVG(load_time) as avg_load_time,
            MAX(load_time) as max_load_time
        FROM performance 
        WHERE timestamp >= ? AND load_time > 0
        GROUP BY app_id
        ORDER BY avg_load_time DESC
    ''', (cutoff,)).fetchall()
    global_stats = conn.execute('''
        SELECT 
            COUNT(*) as total_requests,
            AVG(load_time) as global_avg_load,
            MAX(load_time) as global_max_load
        FROM performance 
        WHERE timestamp >= ? AND load_time > 0
    ''', (cutoff,)).fetchone()
    conn.close()
    return jsonify({
        'period_days': days,
        'global': {
            'total_requests': global_stats['total_requests'] if global_stats else 0,
            'avg_load_time': round(global_stats['global_avg_load'], 2) if global_stats and global_stats['global_avg_load'] else 0,
            'max_load_time': round(global_stats['global_max_load'], 2) if global_stats and global_stats['global_max_load'] else 0
        },
        'apps': [dict(row) for row in apps]
    })