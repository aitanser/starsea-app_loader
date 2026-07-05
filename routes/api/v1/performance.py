from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
from config import DATA_DIR

performance_bp = Blueprint('performance', __name__)
PERF_PATH = os.path.join(DATA_DIR, 'performance.json')

def load_perf_data():
    if os.path.exists(PERF_PATH):
        with open(PERF_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_perf_data(data):
    with open(PERF_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@performance_bp.route('/<app_id>/report', methods=['POST'])
def report_performance(app_id):
    """上报性能数据"""
    data = request.json
    perf_data = load_perf_data()
    if app_id not in perf_data:
        perf_data[app_id] = {'history': []}

    entry = {
        'timestamp': datetime.now().isoformat(),
        'load_time': data.get('load_time', 0),
        'resource_size': data.get('resource_size', 0),
        'request_count': data.get('request_count', 0),
        'user_agent': request.headers.get('User-Agent', '')
    }

    perf_data[app_id]['history'].append(entry)
    # 保留最近100条记录
    if len(perf_data[app_id]['history']) > 100:
        perf_data[app_id]['history'] = perf_data[app_id]['history'][-100:]

    save_perf_data(perf_data)
    return jsonify({'status': 'ok'})

@performance_bp.route('/<app_id>')
def get_performance(app_id):
    """获取应用性能统计"""
    perf_data = load_perf_data()
    if app_id not in perf_data:
        return jsonify({'app_id': app_id, 'history': [], 'stats': {}})

    history = perf_data[app_id]['history']
    if not history:
        return jsonify({'app_id': app_id, 'history': [], 'stats': {}})

    load_times = [h['load_time'] for h in history if h.get('load_time', 0) > 0]
    stats = {
        'count': len(history),
        'avg_load_time': round(sum(load_times) / len(load_times), 2) if load_times else 0,
        'max_load_time': max(load_times) if load_times else 0,
        'min_load_time': min(load_times) if load_times else 0,
        'avg_resource_size': round(sum(h.get('resource_size', 0) for h in history) / len(history), 2)
    }

    return jsonify({
        'app_id': app_id,
        'history': history[-20:],  # 最近20条
        'stats': stats
    })
