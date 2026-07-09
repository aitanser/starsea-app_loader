#!/usr/bin/env python3
# admin.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

from flask import Blueprint, render_template_string, request, session, redirect, jsonify
from functools import wraps
from models import scan_apps, load_favorites, load_notes, save_notes, load_apps_config, save_apps_config, load_framework_config, load_users, save_users
from utils import get_access_logs, get_trend_data
from config import DATA_DIR, CONFIG_PATH, APP_CONFIG_PATH, LOG_PATH, ADMIN_CONFIG_PATH, FAVORITES_PATH, NOTE_PATH
from werkzeug.security import check_password_hash, generate_password_hash
import os
import json
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user') or session.get('role') != 'admin':
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated

# ---------- 根路由 ----------
@admin_bp.route('/')
def admin_root():
    if session.get('user') and session.get('role') == 'admin':
        return redirect('/admin/dashboard')
    return redirect('/admin/login')

# ---------- 登录 ----------
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        users = load_users()
        if username in users and check_password_hash(users[username]['password_hash'], password):
            if users[username].get('role') == 'admin':
                session['user'] = username
                session['role'] = 'admin'
                return redirect('/admin/dashboard')
            else:
                error = '该账户不是管理员'
        else:
            error = '用户名或密码错误'
        return render_template_string(login_html, error=error)
    return render_template_string(login_html, error='')

login_html = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>管理员登录</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-muted: #a09080;
    --accent-primary: #c8983a;
    --border-light: rgba(255,255,255,0.06);
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-muted: #7a6b5d;
    --accent-primary: #c8983a;
    --border-light: rgba(0,0,0,0.06);
}
body{background:var(--bg-secondary);color:var(--text-primary);font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;transition:background 0.25s, color 0.25s;}
.login-box{background:var(--bg-panel);padding:2rem;border-radius:12px;border:1px solid var(--border-light);width:300px;backdrop-filter:blur(8px);}
h1{text-align:center;margin-bottom:1.5rem;}
h1 i{color:var(--accent-primary);}
input{width:100%;padding:0.6rem;margin:0.5rem 0;background:rgba(255,255,255,0.05);border:1px solid var(--border-light);border-radius:6px;color:var(--text-primary);}
button{width:100%;padding:0.6rem;background:var(--accent-primary);border:none;border-radius:6px;color:#1a0f08;font-weight:bold;cursor:pointer;}
.error{color:#e07040;text-align:center;margin-top:0.5rem;}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
</script>
</head>
<body>
<div class="login-box">
<h1><i class="fas fa-crown"></i> 管理员登录</h1>
<form method="POST">
<input type="text" name="username" placeholder="用户名" required>
<input type="password" name="password" placeholder="密码" required>
<button type="submit"><i class="fas fa-sign-in-alt"></i> 登录</button>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
</form>
</div>
</body>
</html>
'''

@admin_bp.route('/logout')
def admin_logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect('/admin/login')

# ---------- 仪表板 ----------
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    apps = scan_apps()
    logs = get_access_logs(50)
    total_access = sum(a.get('access_count', 0) for a in apps)
    enabled_count = sum(1 for a in apps if a.get('enabled', True))
    disabled_count = len(apps) - enabled_count
    total_files = sum(len(a.get('html_files', [])) for a in apps)
    notes = load_notes()

    health_data = {}
    health_path = os.path.join(DATA_DIR, 'health.json')
    if os.path.exists(health_path):
        with open(health_path, 'r', encoding='utf-8') as f:
            health_data = json.load(f)

    try:
        import psutil
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
    except:
        cpu = mem = disk = None

    audit_path = os.path.join(DATA_DIR, 'audit.json')
    audit_logs = []
    if os.path.exists(audit_path):
        with open(audit_path, 'r', encoding='utf-8') as f:
            audit_logs = json.load(f)[-10:]

    return render_template_string(dashboard_html,
        apps=apps,
        enabled_count=enabled_count,
        disabled_count=disabled_count,
        total_files=total_files,
        total_access=total_access,
        logs=logs,
        cpu=cpu,
        mem=mem,
        disk=disk,
        notes=notes,
        health_data=health_data,
        audit_logs=audit_logs
    )

dashboard_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
    <title>管理后台</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-primary: #1a0f08;
            --bg-secondary: #2a1f18;
            --bg-panel: rgba(30,20,15,0.92);
            --bg-card: rgba(255,255,255,0.04);
            --text-primary: #f5e6d3;
            --text-secondary: #d0c0b0;
            --text-muted: #a09080;
            --border-light: rgba(255,255,255,0.06);
            --shadow: 0 2px 12px rgba(0,0,0,0.4);
            --shadow-panel: 0 8px 30px rgba(0,0,0,0.5);
            --accent-primary: #c8983a;
            --accent-secondary: #8fbf6a;
            --accent-gradient: linear-gradient(90deg, #f4c76a, #e89840);
            --radius: 12px;
            --transition: 0.25s ease;
            --btn-text: #1a0f08;
            --badge-on: #2e9453;
            --badge-off: #a83838;
        }
        [data-theme="light"] {
            --bg-primary: #f5f0e8;
            --bg-secondary: #e8e0d6;
            --bg-panel: rgba(255,252,248,0.95);
            --bg-card: rgba(0,0,0,0.04);
            --text-primary: #2a1f18;
            --text-secondary: #4a3728;
            --text-muted: #7a6b5d;
            --border-light: rgba(0,0,0,0.06);
            --shadow: 0 2px 12px rgba(0,0,0,0.08);
            --shadow-panel: 0 8px 30px rgba(0,0,0,0.12);
            --btn-text: #f5f0e8;
        }
        [data-theme-color="warm"] { --accent-primary: #c8983a; --accent-secondary: #8fbf6a; --accent-gradient: linear-gradient(90deg, #f4c76a, #e89840); }
        [data-theme-color="mint"] { --accent-primary: #4dab9e; --accent-secondary: #6abf8a; --accent-gradient: linear-gradient(90deg, #6abf8a, #4dab9e); }
        [data-theme-color="indigo"] { --accent-primary: #7c8fc0; --accent-secondary: #a8b8d8; --accent-gradient: linear-gradient(90deg, #a8b8d8, #7c8fc0); }
        [data-theme-color="rose"] { --accent-primary: #d4878a; --accent-secondary: #e8b0b2; --accent-gradient: linear-gradient(90deg, #e8b0b2, #d4878a); }

        * { margin:0; padding:0; box-sizing:border-box; }
        body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: background var(--transition), color var(--transition); display: flex; min-height: 100vh; }
        .sidebar {
            width: 240px;
            background: var(--bg-panel);
            border-right: 1px solid var(--border-light);
            padding: 1.5rem 1rem;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            backdrop-filter: blur(8px);
            transition: transform var(--transition);
            z-index: 10;
        }
        .sidebar .logo { font-size: 1.3rem; font-weight: 600; color: var(--text-primary); padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
        .sidebar .logo i { color: var(--accent-primary); }
        .sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
        .sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
        .sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
        .sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
        .sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
        .hamburger {
            display: none;
            background: none;
            border: none;
            color: var(--text-primary);
            font-size: 1.5rem;
            padding: 0.5rem;
            cursor: pointer;
            position: fixed;
            top: 0.5rem;
            left: 0.5rem;
            z-index: 20;
        }
        .main-content { flex: 1; padding: 1.5rem; overflow-x: hidden; background: var(--bg-primary); }
        .page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
        .stat-card { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1rem; text-align: center; box-shadow: var(--shadow); transition: all var(--transition); backdrop-filter: blur(4px); }
        .stat-card .number { font-size: 2rem; font-weight: bold; color: var(--accent-primary); }
        .stat-card .label { color: var(--text-muted); font-size: 0.85rem; }
        .health-grid { display: flex; flex-wrap: wrap; gap: 0.8rem; margin-bottom: 1.5rem; }
        .health-item { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 0.6rem 1rem; display: flex; align-items: center; gap: 0.6rem; font-size: 0.85rem; color: var(--text-muted); backdrop-filter: blur(4px); }
        .health-item .val { font-weight: bold; color: var(--text-primary); }
        .health-item .status-ok { color: var(--badge-on); }
        .health-item .status-fail { color: var(--badge-off); }
        .section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow); backdrop-filter: blur(4px); }
        .section h2 { color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 1rem; }
        .section h2 i { margin-right: 0.5rem; color: var(--accent-primary); }
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        th { text-align: left; color: var(--text-muted); padding: 0.4rem; border-bottom: 1px solid var(--border-light); }
        td { padding: 0.4rem; border-bottom: 1px solid var(--border-light); color: var(--text-primary); }
        tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
        .btn-sm { padding: 0.2rem 0.8rem; font-size: 0.75rem; border: none; border-radius: 4px; cursor: pointer; color: #1a0f08; margin: 0 2px; transition: opacity var(--transition); min-height: 32px; }
        .btn-sm.green { background: var(--badge-on); }
        .btn-sm.red { background: var(--badge-off); }
        .btn-sm.blue { background: var(--accent-primary); }
        .btn-sm.gold { background: #b88626; }
        .btn-sm:hover { opacity: 0.8; }
        .status-badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 500; }
        .status-badge.on { background: var(--badge-on); color: #fff; }
        .status-badge.off { background: var(--badge-off); color: #fff; }
        .log-container { max-height: 300px; overflow-y: auto; font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }
        .log-entry { padding: 0.2rem 0; border-bottom: 1px solid var(--border-light); }
        .batch-bar { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin-top: 0.5rem; }
        .batch-bar .btn-sm { padding: 0.2rem 0.8rem; font-size: 0.8rem; }
        .chart-container { max-height: 200px; margin: 0.5rem 0; }
        .backup-bar { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
        .responsive-table { overflow-x: auto; -webkit-overflow-scrolling: touch; }
        .responsive-table table { min-width: 600px; }
        .sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
        .sidebar-overlay.open { display: block; }

        @media (max-width: 768px) {
            body { flex-direction: column; }
            .hamburger { display: block; }
            .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
            .sidebar.open { transform: translateX(0); }
            .main-content { padding: 1rem; margin-top: 3rem; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .health-grid { flex-direction: column; }
        }
        @media (max-width: 480px) {
            .stats-grid { grid-template-columns: 1fr 1fr; }
            .stat-card .number { font-size: 1.5rem; }
            .btn-sm { font-size: 0.7rem; padding: 0.1rem 0.5rem; min-height: 28px; }
        }
    </style>
    <script>
        (function() {
            const t = localStorage.getItem('ui-theme') || 'dark';
            const c = localStorage.getItem('ui-color') || 'warm';
            document.documentElement.setAttribute('data-theme', t);
            document.documentElement.setAttribute('data-theme-color', c);
        })();

        function toggleSidebar() {
            document.querySelector('.sidebar').classList.toggle('open');
            document.querySelector('.sidebar-overlay').classList.toggle('open');
        }
        function closeSidebar() {
            document.querySelector('.sidebar').classList.remove('open');
            document.querySelector('.sidebar-overlay').classList.remove('open');
        }

        function toggleApp(appId, enable) {
            fetch('/api/v1/apps/' + appId + '/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enable })
            })
            .then(r => r.json())
            .then(data => { if (data.status === 'ok') location.reload(); else alert('操作失败'); })
            .catch(() => alert('网络错误'));
        }
        function deleteApp(appId) {
            if (!confirm('确认删除此应用及其目录？')) return;
            fetch('/api/v1/apps/' + appId, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => { if (data.status === 'ok') location.reload(); else alert('删除失败'); })
            .catch(() => alert('网络错误'));
        }
        function openApp(appId) {
            window.open('/app/' + encodeURIComponent(appId) + '/', '_blank');
        }
        function editNote(appId, current) {
            const newNote = prompt('请输入备注：', current || '');
            if (newNote === null) return;
            fetch('/api/v1/note/' + appId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ note: newNote })
            })
            .then(r => r.json())
            .then(data => { if (data.status === 'ok') location.reload(); else alert('保存失败'); })
            .catch(() => alert('网络错误'));
        }
        function backupData() {
            if (!confirm('备份所有配置数据？')) return;
            fetch('/api/v1/system/backup', { method: 'POST' })
            .then(r => r.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'backup_' + new Date().toISOString().slice(0,10) + '.zip';
                a.click();
                URL.revokeObjectURL(url);
            })
            .catch(() => alert('备份失败'));
        }
        function restoreData() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.zip';
            input.onchange = function(e) {
                const file = e.target.files[0];
                if (!file) return;
                const formData = new FormData();
                formData.append('file', file);
                fetch('/api/v1/system/restore', {
                    method: 'POST',
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'ok') {
                        alert('恢复成功！');
                        location.reload();
                    } else {
                        alert('恢复失败：' + data.error);
                    }
                })
                .catch(() => alert('网络错误'));
            };
            input.click();
        }
        function importApp() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.zip';
            input.onchange = function(e) {
                const file = e.target.files[0];
                if (!file) return;
                const formData = new FormData();
                formData.append('file', file);
                fetch('/api/v1/apps/import', {
                    method: 'POST',
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'ok') {
                        alert('导入成功！应用 ID: ' + data.app_id);
                        location.reload();
                    } else {
                        alert('导入失败：' + data.error);
                    }
                })
                .catch(() => alert('网络错误'));
            };
            input.click();
        }
        function batchAction(action) {
            const checks = document.querySelectorAll('input[name="app_select"]:checked');
            if (checks.length === 0) { alert('请至少选择一个应用'); return; }
            const ids = Array.from(checks).map(c => c.value);
            if (action === 'delete') {
                if (!confirm('确定要永久删除 ' + ids.length + ' 个应用吗？')) return;
                fetch('/api/v1/apps/batch', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids: ids })
                })
                .then(r => r.json())
                .then(data => { if (data.status === 'ok') location.reload(); else alert('操作失败'); })
                .catch(() => alert('网络错误'));
                return;
            }
            const enable = (action === 'enable');
            if (!confirm('确定要对 ' + ids.length + ' 个应用执行 "' + action + '" 操作吗？')) return;
            fetch('/api/v1/apps/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: ids, enabled: enable })
            })
            .then(r => r.json())
            .then(data => { if (data.status === 'ok') location.reload(); else alert('操作失败'); })
            .catch(() => alert('网络错误'));
        }
        function selectAll() {
            const checks = document.querySelectorAll('input[name="app_select"]');
            const allChecked = Array.from(checks).every(c => c.checked);
            checks.forEach(c => c.checked = !allChecked);
        }

        fetch('/api/v1/stats/trend')
            .then(r => r.json())
            .then(data => {
                new Chart(document.getElementById('trendChart'), {
                    type: 'line',
                    data: {
                        labels: data.dates,
                        datasets: [{
                            label: '访问量',
                            data: data.values,
                            borderColor: getComputedStyle(document.documentElement).getPropertyValue('--accent-primary').trim() || '#c8983a',
                            fill: false,
                            tension: 0.3
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { display: false } } }
                });
            });
    </script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar" id="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard" class="active"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>

    <div class="main-content">
        <div class="page-title"><i class="fas fa-chart-pie"></i> 总览</div>
        <div class="health-grid">
            <div class="health-item"><i class="fas fa-microchip"></i> CPU：<span class="val">{{ cpu if cpu is not none else 'N/A' }}%</span></div>
            <div class="health-item"><i class="fas fa-memory"></i> 内存：<span class="val">{{ mem if mem is not none else 'N/A' }}%</span></div>
            <div class="health-item"><i class="fas fa-hdd"></i> 磁盘：<span class="val">{{ disk if disk is not none else 'N/A' }}%</span></div>
            <div class="health-item"><i class="fas fa-cube"></i> 应用数：<span class="val">{{ apps|length }}</span></div>
            <div class="health-item"><i class="fas fa-check-circle"></i> 健康应用：<span class="val">{{ health_data.values()|selectattr('status','equalto','healthy')|list|length }}</span></div>
            <div class="health-item"><i class="fas fa-exclamation-triangle"></i> 异常：<span class="val">{{ health_data.values()|selectattr('status','equalto','unhealthy')|list|length }}</span></div>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><div class="number">{{ apps|length }}</div><div class="label"><i class="fas fa-cube"></i> 应用总数</div></div>
            <div class="stat-card"><div class="number">{{ enabled_count }}</div><div class="label"><i class="fas fa-check-circle" style="color:var(--badge-on);"></i> 已启用</div></div>
            <div class="stat-card"><div class="number">{{ disabled_count }}</div><div class="label"><i class="fas fa-ban" style="color:var(--badge-off);"></i> 已禁用</div></div>
            <div class="stat-card"><div class="number">{{ total_files }}</div><div class="label"><i class="fas fa-file-code"></i> HTML 文件</div></div>
            <div class="stat-card"><div class="number">{{ total_access }}</div><div class="label"><i class="fas fa-eye"></i> 总访问次数</div></div>
            <div class="stat-card"><div class="number">{{ logs|length }}</div><div class="label"><i class="fas fa-list"></i> 最近日志条数</div></div>
        </div>

        <div class="section">
            <h2><i class="fas fa-chart-line"></i> 访问趋势（近30天）</h2>
            <div class="chart-container"><canvas id="trendChart" height="100"></canvas></div>
        </div>

        <div class="section">
            <h2><i class="fas fa-database"></i> 数据备份与恢复</h2>
            <div class="backup-bar">
                <button class="btn-sm blue" onclick="backupData()"><i class="fas fa-download"></i> 备份数据</button>
                <button class="btn-sm green" onclick="restoreData()"><i class="fas fa-upload"></i> 恢复数据</button>
                <button class="btn-sm gold" onclick="importApp()"><i class="fas fa-upload"></i> 导入应用</button>
            </div>
        </div>

        <div class="section">
            <h2><i class="fas fa-th-list"></i> 应用列表</h2>
            <div class="batch-bar">
                <button class="btn-sm green" onclick="batchAction('enable')"><i class="fas fa-check"></i> 批量启用</button>
                <button class="btn-sm red" onclick="batchAction('disable')"><i class="fas fa-ban"></i> 批量禁用</button>
                <button class="btn-sm red" onclick="batchAction('delete')"><i class="fas fa-trash"></i> 批量删除</button>
                <button class="btn-sm blue" onclick="selectAll()"><i class="fas fa-check-double"></i> 全选</button>
            </div>
            <div class="responsive-table">
                <table>
                    <thead>
                        <tr>
                            <th style="width:30px;"><input type="checkbox" onclick="selectAll()"></th>
                            <th>应用</th><th>ID</th><th>分类</th><th>版本</th>
                            <th>类型</th>
                            <th>页面</th><th>状态</th><th>访问</th><th>备注</th><th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for app in apps %}
                    <tr>
                        <td><input type="checkbox" name="app_select" value="{{ app.id }}"></td>
                        <td><i class="fas {{ app.icon_class }}"></i> {{ app.name }}</td>
                        <td style="color:var(--text-muted);font-size:0.8rem;">{{ app.id }}</td>
                        <td><span style="font-size:0.7rem;padding:0.1rem 0.4rem;border-radius:10px;background:var(--bg-card);border:1px solid var(--border-light);">{{ app.category }}</span></td>
                        <td>{{ app.version }}</td>
                        <td><span class="badge" style="background:var(--bg-card);padding:0.1rem 0.4rem;border-radius:4px;font-size:0.7rem;">{{ app.app_type }}</span></td>
                        <td>{{ app.html_files|length }}</td>
                        <td><span class="status-badge {{ 'on' if app.enabled else 'off' }}">{{ '启用' if app.enabled else '禁用' }}</span></td>
                        <td>{{ app.access_count }}</td>
                        <td>
                            <span style="font-size:0.8rem;color:var(--text-muted);cursor:pointer;" onclick="editNote('{{ app.id }}', '{{ notes.get(app.id, '') }}')" title="点击编辑备注">
                                <i class="fas fa-edit"></i> {{ notes.get(app.id, '') or '添加备注' }}
                            </span>
                        </td>
                        <td>
                            <button class="btn-sm blue" onclick="toggleApp('{{ app.id }}', {{ 'false' if app.enabled else 'true' }})"><i class="fas {{ 'fa-ban' if app.enabled else 'fa-check' }}"></i> {{ '禁用' if app.enabled else '启用' }}</button>
                            <button class="btn-sm green" onclick="openApp('{{ app.id }}')"><i class="fas fa-external-link-alt"></i> 打开</button>
                            <button class="btn-sm red" onclick="deleteApp('{{ app.id }}')"><i class="fas fa-trash"></i></button>
                            <button class="btn-sm gold" onclick="window.open('/api/v1/apps/{{ app.id }}/export','_blank')"><i class="fas fa-download"></i> 导出</button>
                        </td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2><i class="fas fa-history"></i> 最近访问日志</h2>
            <div class="log-container">
                {% for log in logs %}<div class="log-entry">{{ log }}</div>{% else %}<div style="color:var(--text-muted);"><i class="fas fa-info-circle"></i> 暂无日志</div>{% endfor %}
            </div>
        </div>

        <div class="section">
            <h2><i class="fas fa-clipboard-list"></i> 最近审计日志</h2>
            <div class="log-container">
                {% for entry in audit_logs %}
                <div class="log-entry">{{ entry.timestamp }} - {{ entry.user }}: {{ entry.action }} {% if entry.app_id %}({{ entry.app_id }}){% endif %}</div>
                {% else %}
                <div style="color:var(--text-muted);"><i class="fas fa-info-circle"></i> 暂无审计记录</div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
'''

# ---------- 应用管理 ----------
@admin_bp.route('/apps')
@admin_required
def admin_apps():
    apps = scan_apps()
    notes = load_notes()
    return render_template_string(apps_html, apps=apps, notes=notes)

apps_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>应用管理</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --bg-card: rgba(255,255,255,0.04);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
    --badge-on: #2e9453;
    --badge-off: #a83838;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --bg-card: rgba(0,0,0,0.04);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: all var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; box-shadow: var(--shadow); margin-bottom: 1.5rem; backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); margin-bottom: 1rem; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 0.4rem; border-bottom: 1px solid var(--border-light); text-align: left; }
tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
.status-badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 500; }
.status-badge.on { background: var(--badge-on); color: #fff; }
.status-badge.off { background: var(--badge-off); color: #fff; }
.btn-sm { padding: 0.1rem 0.6rem; font-size: 0.7rem; border: none; border-radius: 4px; cursor: pointer; color: #1a0f08; margin: 0 2px; transition: opacity 0.25s; }
.btn-sm.green { background: var(--badge-on); }
.btn-sm.blue { background: var(--accent-primary); }
.btn-sm:hover { opacity: 0.8; }
.back-link { color: var(--accent-primary); text-decoration: none; margin-top: 1rem; display: inline-block; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
    .responsive-table { overflow-x: auto; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
    function openApp(appId) { window.open('/app/' + encodeURIComponent(appId) + '/', '_blank'); }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps" class="active"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-th"></i> 应用管理</div>
        <div class="section">
            <table>
                <thead>
                    <tr>
                        <th>名称</th><th>ID</th><th>分类</th><th>版本</th>
                        <th>类型</th>
                        <th>状态</th><th>操作</th>
                    </tr>
                </thead>
                <tbody>
                {% for app in apps %}
                <tr>
                    <td><i class="fas {{ app.icon_class }}"></i> {{ app.name }}</td>
                    <td style="color:var(--text-muted);">{{ app.id }}</td>
                    <td>{{ app.category }}</td>
                    <td>{{ app.version }}</td>
                    <td><span class="badge" style="background:var(--bg-card);padding:0.1rem 0.4rem;border-radius:4px;font-size:0.7rem;">{{ app.app_type }}</span></td>
                    <td><span class="status-badge {{ 'on' if app.enabled else 'off' }}">{{ '启用' if app.enabled else '禁用' }}</span></td>
                    <td><button class="btn-sm green" onclick="openApp('{{ app.id }}')"><i class="fas fa-external-link-alt"></i> 打开</button></td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
        <a href="/admin/dashboard" class="back-link"><i class="fas fa-arrow-left"></i> 返回总览</a>
    </div>
</body>
</html>
'''

# ---------- 访问日志 ----------
@admin_bp.route('/logs')
@admin_required
def admin_logs():
    logs = get_access_logs(500)
    return render_template_string(logs_html, logs=logs)

logs_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>访问日志</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: all var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; box-shadow: var(--shadow); margin-bottom: 1.5rem; backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); margin-bottom: 1rem; }
.log-container { max-height: 600px; overflow-y: auto; font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }
.log-entry { padding: 0.2rem 0; border-bottom: 1px solid var(--border-light); }
.back-link { color: var(--accent-primary); text-decoration: none; margin-top: 1rem; display: inline-block; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs" class="active"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-history"></i> 访问日志</div>
        <div class="section">
            <h2>最近 500 条日志</h2>
            <div class="log-container">
                {% for log in logs %}<div class="log-entry">{{ log }}</div>{% else %}<div style="color:var(--text-muted);"><i class="fas fa-info-circle"></i> 暂无日志</div>{% endfor %}
            </div>
        </div>
        <a href="/admin/dashboard" class="back-link"><i class="fas fa-arrow-left"></i> 返回总览</a>
    </div>
</body>
</html>
'''

# ---------- 设置 ----------
@admin_bp.route('/settings')
@admin_required
def admin_settings():
    config = load_framework_config()
    return render_template_string(settings_html,
        config=config,
        data_dir=DATA_DIR,
        config_path=CONFIG_PATH,
        app_config_path=APP_CONFIG_PATH,
        log_path=LOG_PATH,
        admin_config_path=ADMIN_CONFIG_PATH,
        favorites_path=FAVORITES_PATH
    )

settings_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>设置</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: all var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; box-shadow: var(--shadow); margin-bottom: 1.5rem; backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); margin-bottom: 1rem; }
.info-row { display: flex; padding: 0.4rem 0; border-bottom: 1px solid var(--border-light); }
.info-row .key { width: 150px; color: var(--text-muted); }
.info-row .value { color: var(--text-primary); }
.back-link { color: var(--accent-primary); text-decoration: none; margin-top: 1rem; display: inline-block; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings" class="active"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-sliders-h"></i> 设置</div>
        <div class="section">
            <h2>框架配置</h2>
            <div class="info-row"><span class="key">监听端口</span><span class="value">{{ config.port }}</span></div>
            <div class="info-row"><span class="key">应用目录</span><span class="value">{{ config.apps_dir }}</span></div>
            <div class="info-row"><span class="key">框架版本</span><span class="value">{{ config.version }}</span></div>
            <div class="info-row"><span class="key">数据目录</span><span class="value">{{ data_dir }}</span></div>
            <div style="margin-top:1.5rem;color:var(--text-muted);font-size:0.9rem;">
                <i class="fas fa-info-circle"></i> 配置文件：{{ config_path }}
                <br><i class="fas fa-info-circle"></i> 应用配置：{{ app_config_path }}
                <br><i class="fas fa-info-circle"></i> 日志文件：{{ log_path }}
                <br><i class="fas fa-info-circle"></i> 密码存储在：{{ admin_config_path }}
                <br><i class="fas fa-info-circle"></i> 收藏存储在：{{ favorites_path }}
                <br><i class="fas fa-info-circle"></i> 可在"修改密码"页面更改密码
            </div>
        </div>
        <a href="/admin/dashboard" class="back-link"><i class="fas fa-arrow-left"></i> 返回总览</a>
    </div>
</body>
</html>
'''

# ---------- 修改密码 ----------
@admin_bp.route('/change-password', methods=['GET', 'POST'])
@admin_required
def admin_change_password():
    error = None
    success = None
    if request.method == 'POST':
        old = request.form.get('old_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        users = load_users()
        current_user = session.get('user')
        if current_user not in users:
            error = '用户不存在'
        elif not check_password_hash(users[current_user]['password_hash'], old):
            error = '旧密码错误'
        elif len(new) < 4:
            error = '新密码长度至少4位'
        elif new != confirm:
            error = '两次输入的新密码不一致'
        else:
            from werkzeug.security import generate_password_hash
            users[current_user]['password_hash'] = generate_password_hash(new)
            users[current_user]['password_changed'] = True
            save_users(users)
            success = '密码修改成功'
    return render_template_string(change_pw_html, error=error, success=success)

change_pw_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>修改密码</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: all var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; box-shadow: var(--shadow); margin-bottom: 1.5rem; backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); margin-bottom: 1rem; }
.form-group { margin: 1rem 0; }
.form-group label { display: block; color: var(--text-secondary); margin-bottom: 0.3rem; font-size: 0.9rem; }
.form-group input { width: 100%; padding: 0.6rem; background: rgba(255,255,255,0.05); border: 1px solid var(--border-light); border-radius: 6px; color: var(--text-primary); font-size: 1rem; transition: border-color var(--transition), background var(--transition); }
.form-group input:focus { border-color: var(--accent-primary); outline: none; }
.btn { width: 100%; padding: 0.7rem; background: var(--accent-primary); border: none; border-radius: 6px; color: var(--btn-text); font-size: 1rem; cursor: pointer; transition: background var(--transition); }
.btn:hover { opacity: 0.9; }
.error { color: #e07040; text-align: center; margin-top: 0.5rem; }
.success { color: var(--badge-on, #2e9453); text-align: center; margin-top: 0.5rem; }
.back-link { color: var(--accent-primary); text-decoration: none; margin-top: 1rem; display: inline-block; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password" class="active"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-key"></i> 修改密码</div>
        <div class="section">
            <form method="POST">
                <div class="form-group"><label>当前密码</label><input type="password" name="old_password" required></div>
                <div class="form-group"><label>新密码（至少4位）</label><input type="password" name="new_password" required minlength="4"></div>
                <div class="form-group"><label>确认新密码</label><input type="password" name="confirm_password" required minlength="4"></div>
                <button type="submit" class="btn"><i class="fas fa-save"></i> 修改密码</button>
                {% if error %}<div class="error"><i class="fas fa-exclamation-circle"></i> {{ error }}</div>{% endif %}
                {% if success %}<div class="success"><i class="fas fa-check-circle"></i> {{ success }}</div>{% endif %}
            </form>
        </div>
        <a href="/admin/dashboard" class="back-link"><i class="fas fa-arrow-left"></i> 返回总览</a>
    </div>
</body>
</html>
'''

# ---------- 用户管理 ----------
@admin_bp.route('/users')
@admin_required
def admin_users():
    users = load_users()
    return render_template_string(user_mgmt_html, users=users)

user_mgmt_html = '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>用户管理</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --accent-primary: #c8983a;
    --radius: 12px;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
body{background:var(--bg-secondary);color:var(--text-primary);font-family:sans-serif;padding:20px;transition:background 0.25s, color 0.25s;}
table{width:100%;border-collapse:collapse;}
th,td{padding:8px 12px;border-bottom:1px solid var(--border-light);text-align:left;}
th{color:var(--text-muted);}
.btn{padding:4px 12px;border:none;border-radius:4px;cursor:pointer;margin:0 4px;color:#1a0f08;}
.btn-edit{background:var(--accent-primary);}
.btn-del{background:#e07040;color:#fff;}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
</script>
</head>
<body>
<h1><i class="fas fa-users" style="color:var(--accent-primary);"></i> 用户管理</h1>
<table>
<tr><th>用户名</th><th>角色</th><th>创建时间</th><th>操作</th></tr>
{% for username, info in users.items() %}
<tr>
<td>{{ username }}</td>
<td>{{ info.role }}</td>
<td>{{ info.created }}</td>
<td>
  <form method="POST" action="/admin/users/{{ username }}/role" style="display:inline;">
    <select name="role">
      <option value="user" {% if info.role=='user' %}selected{% endif %}>user</option>
      <option value="admin" {% if info.role=='admin' %}selected{% endif %}>admin</option>
    </select>
    <button type="submit" class="btn btn-edit"><i class="fas fa-save"></i></button>
  </form>
  <form method="POST" action="/admin/users/{{ username }}/delete" style="display:inline;" onsubmit="return confirm('确认删除？')">
    <button type="submit" class="btn btn-del"><i class="fas fa-trash"></i></button>
  </form>
</td>
</tr>
{% endfor %}
</table>
<br>
<a href="/" style="color:var(--accent-primary);">← 返回首页</a>
</body>
</html>
'''

@admin_bp.route('/users/<username>/role', methods=['POST'])
@admin_required
def change_user_role(username):
    new_role = request.form.get('role')
    if new_role not in ('user', 'admin'):
        return jsonify({'error': '无效角色'}), 400
    users = load_users()
    if username not in users:
        return jsonify({'error': '用户不存在'}), 404
    if username == session.get('user'):
        return jsonify({'error': '不能修改自己的角色'}), 400
    users[username]['role'] = new_role
    save_users(users)
    return redirect('/admin/users')

@admin_bp.route('/users/<username>/delete', methods=['POST'])
@admin_required
def delete_user(username):
    users = load_users()
    if username not in users:
        return jsonify({'error': '用户不存在'}), 404
    if username == session.get('user'):
        return jsonify({'error': '不能删除自己'}), 400
    del users[username]
    save_users(users)
    return redirect('/admin/users')

# ---------- 审计日志 ----------
@admin_bp.route('/audit')
@admin_required
def admin_audit():
    audit_path = os.path.join(DATA_DIR, 'audit.json')
    logs = []
    if os.path.exists(audit_path):
        with open(audit_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    return render_template_string(audit_html, logs=logs[-200:])

audit_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>审计日志</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.5);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.12);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: background var(--transition), color var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); transition: transform var(--transition); z-index: 10; }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; overflow-x: hidden; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow); backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 1rem; }
.section h2 i { margin-right: 0.5rem; color: var(--accent-primary); }
.log-container { max-height: 600px; overflow-y: auto; font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }
.log-entry { padding: 0.2rem 0; border-bottom: 1px solid var(--border-light); }
.btn-sm { padding: 0.2rem 0.8rem; font-size: 0.75rem; border: none; border-radius: 4px; cursor: pointer; color: #1a0f08; margin: 0 2px; transition: opacity var(--transition); min-height: 32px; }
.btn-sm.blue { background: var(--accent-primary); }
.btn-sm:hover { opacity: 0.8; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit" class="active"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-clipboard-list"></i> 审计日志</div>
        <div class="section">
            <h2>最近 200 条操作记录</h2>
            <div class="log-container">
                {% for entry in logs %}
                <div class="log-entry">{{ entry.timestamp }} - <strong>{{ entry.user }}</strong> {{ entry.action }} {% if entry.app_id %}(应用: {{ entry.app_id }}){% endif %} {% if entry.details %}{{ entry.details }}{% endif %}</div>
                {% else %}
                <div style="color:var(--text-muted);"><i class="fas fa-info-circle"></i> 暂无审计记录</div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
'''

# ---------- 健康检查 ----------
@admin_bp.route('/health')
@admin_required
def admin_health():
    health_path = os.path.join(DATA_DIR, 'health.json')
    data = {}
    if os.path.exists(health_path):
        with open(health_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return render_template_string(health_html, health=data)

health_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>健康检查</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.5);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.12);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: background var(--transition), color var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); transition: transform var(--transition); z-index: 10; }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; overflow-x: hidden; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow); backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 1rem; }
.section h2 i { margin-right: 0.5rem; color: var(--accent-primary); }
.responsive-table { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th { text-align: left; color: var(--text-muted); padding: 0.4rem; border-bottom: 1px solid var(--border-light); }
td { padding: 0.4rem; border-bottom: 1px solid var(--border-light); color: var(--text-primary); }
tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
.status-badge { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 500; }
.status-badge.on { background: #2e9453; color: #fff; }
.status-badge.off { background: #a83838; color: #fff; }
.btn-sm { padding: 0.2rem 0.8rem; font-size: 0.75rem; border: none; border-radius: 4px; cursor: pointer; color: #1a0f08; margin: 0 2px; transition: opacity var(--transition); min-height: 32px; }
.btn-sm.blue { background: var(--accent-primary); }
.btn-sm:hover { opacity: 0.8; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
    function refreshHealth() {
        fetch('/api/v1/health/check/all')
            .then(r => r.json())
            .then(data => {
                alert('已刷新健康状态');
                location.reload();
            })
            .catch(() => alert('刷新失败'));
    }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health" class="active"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-heartbeat"></i> 健康检查</div>
        <button class="btn-sm blue" onclick="refreshHealth()"><i class="fas fa-sync"></i> 刷新所有</button>
        <div class="section">
            <div class="responsive-table">
                <table>
                    <thead><tr><th>应用</th><th>状态</th><th>消息</th><th>最后检查</th></tr></thead>
                    <tbody>
                    {% for app_id, info in health.items() %}
                    <tr>
                        <td>{{ info.app_name }} ({{ app_id }})</td>
                        <td><span class="status-badge {{ 'on' if info.status == 'healthy' else 'off' }}">{{ info.status }}</span></td>
                        <td>{{ info.message }}</td>
                        <td>{{ info.last_check }}</td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" class="placeholder-text">暂无健康数据，请点击"刷新所有"</td></tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''

# ---------- 版本管理 ----------
@admin_bp.route('/versions')
@admin_required
def admin_versions():
    backup_dir = os.path.join(DATA_DIR, 'backups', 'apps')
    versions = {}
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.endswith('.zip'):
                parts = f.rsplit('_', 1)
                if len(parts) == 2:
                    app_id = parts[0]
                    timestamp = parts[1].replace('.zip', '')
                    if app_id not in versions:
                        versions[app_id] = []
                    versions[app_id].append({
                        'filename': f,
                        'timestamp': timestamp,
                        'size': os.path.getsize(os.path.join(backup_dir, f))
                    })
    return render_template_string(versions_html, versions=versions)

versions_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>版本管理</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.5);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.12);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: background var(--transition), color var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); transition: transform var(--transition); z-index: 10; }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; overflow-x: hidden; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow); backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 1rem; }
.section h2 i { margin-right: 0.5rem; color: var(--accent-primary); }
.responsive-table { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th { text-align: left; color: var(--text-muted); padding: 0.4rem; border-bottom: 1px solid var(--border-light); }
td { padding: 0.4rem; border-bottom: 1px solid var(--border-light); color: var(--text-primary); }
tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
.btn-sm { padding: 0.2rem 0.8rem; font-size: 0.75rem; border: none; border-radius: 4px; cursor: pointer; color: #1a0f08; margin: 0 2px; transition: opacity var(--transition); min-height: 32px; }
.btn-sm.blue { background: var(--accent-primary); }
.btn-sm.gold { background: #b88626; }
.btn-sm:hover { opacity: 0.8; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
    function createBackup(appId) {
        if (!confirm('为 ' + appId + ' 创建备份？')) return;
        fetch('/api/v1/versions/' + appId + '/backup', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'ok') { alert('备份成功'); location.reload(); }
                else alert('备份失败：' + data.error);
            })
            .catch(() => alert('网络错误'));
    }
    function rollback(appId, filename) {
        if (!confirm('回滚到 ' + filename + ' ？')) return;
        fetch('/api/v1/versions/' + appId + '/rollback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: filename })
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') { alert('回滚成功'); location.reload(); }
            else alert('回滚失败：' + data.error);
        })
        .catch(() => alert('网络错误'));
    }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions" class="active"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-code-branch"></i> 版本管理</div>
        {% for app_id, backups in versions.items() %}
        <div class="section">
            <h2><i class="fas fa-cube"></i> {{ app_id }} <button class="btn-sm blue" onclick="createBackup('{{ app_id }}')"><i class="fas fa-plus"></i> 创建备份</button></h2>
            <div class="responsive-table">
                <table>
                    <thead><tr><th>文件名</th><th>时间戳</th><th>大小</th><th>操作</th></tr></thead>
                    <tbody>
                    {% for b in backups|sort(attribute='timestamp', reverse=true) %}
                    <tr>
                        <td>{{ b.filename }}</td>
                        <td>{{ b.timestamp }}</td>
                        <td>{{ (b.size / 1024)|round(1) }} KB</td>
                        <td><button class="btn-sm gold" onclick="rollback('{{ app_id }}', '{{ b.filename }}')"><i class="fas fa-undo"></i> 回滚</button></td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% else %}
        <div class="section"><p class="placeholder-text">暂无版本备份，请先为应用创建备份。</p></div>
        {% endfor %}
    </div>
</body>
</html>
'''

# ---------- 标签管理 ----------
@admin_bp.route('/tags')
@admin_required
def admin_tags():
    apps = scan_apps()
    tag_count = {}
    for app in apps:
        for tag in app.get('tags', []):
            tag_count[tag] = tag_count.get(tag, 0) + 1
    return render_template_string(tags_html, tags=tag_count)

tags_html = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>标签管理</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root {
    --bg-primary: #1a0f08;
    --bg-secondary: #2a1f18;
    --bg-panel: rgba(30,20,15,0.92);
    --text-primary: #f5e6d3;
    --text-secondary: #d0c0b0;
    --text-muted: #a09080;
    --border-light: rgba(255,255,255,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.5);
    --accent-primary: #c8983a;
    --radius: 12px;
    --transition: 0.25s ease;
    --btn-text: #1a0f08;
}
[data-theme="light"] {
    --bg-primary: #f5f0e8;
    --bg-secondary: #e8e0d6;
    --bg-panel: rgba(255,252,248,0.95);
    --text-primary: #2a1f18;
    --text-secondary: #4a3728;
    --text-muted: #7a6b5d;
    --border-light: rgba(0,0,0,0.06);
    --shadow: 0 2px 12px rgba(0,0,0,0.08);
    --shadow-panel: 0 8px 30px rgba(0,0,0,0.12);
    --btn-text: #f5f0e8;
}
[data-theme-color="warm"] { --accent-primary: #c8983a; }
[data-theme-color="mint"] { --accent-primary: #4dab9e; }
[data-theme-color="indigo"] { --accent-primary: #7c8fc0; }
[data-theme-color="rose"] { --accent-primary: #d4878a; }
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg-secondary); color: var(--text-primary); font-family: system-ui, sans-serif; transition: background var(--transition), color var(--transition); display: flex; min-height: 100vh; }
.sidebar { width: 240px; background: var(--bg-panel); border-right: 1px solid var(--border-light); padding: 1.5rem 1rem; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem; backdrop-filter: blur(8px); transition: transform var(--transition); z-index: 10; }
.sidebar .logo { font-size: 1.3rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-light); }
.sidebar .logo i { color: var(--accent-primary); }
.sidebar nav { display: flex; flex-direction: column; gap: 0.3rem; }
.sidebar nav a { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; color: var(--text-secondary); text-decoration: none; transition: all var(--transition); font-size: 0.9rem; }
.sidebar nav a:hover { background: rgba(255,255,255,0.06); color: var(--accent-primary); }
.sidebar nav a.active { background: var(--accent-primary); color: var(--btn-text); }
.sidebar .user-info { margin-top: auto; border-top: 1px solid var(--border-light); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); }
.hamburger { display: none; background: none; border: none; color: var(--text-primary); font-size: 1.5rem; padding: 0.5rem; cursor: pointer; position: fixed; top: 0.5rem; left: 0.5rem; z-index: 20; }
.main-content { flex: 1; padding: 1.5rem; overflow-x: hidden; background: var(--bg-primary); }
.page-title { font-size: 1.5rem; margin-bottom: 1.5rem; color: var(--text-primary); }
.section { background: var(--bg-panel); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow); backdrop-filter: blur(4px); }
.section h2 { color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 1rem; }
.section h2 i { margin-right: 0.5rem; color: var(--accent-primary); }
.responsive-table { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th { text-align: left; color: var(--text-muted); padding: 0.4rem; border-bottom: 1px solid var(--border-light); }
td { padding: 0.4rem; border-bottom: 1px solid var(--border-light); color: var(--text-primary); }
tr:nth-child(even) td { background: rgba(255,255,255,0.02); }
.btn-sm { padding: 0.2rem 0.8rem; font-size: 0.75rem; border: none; border-radius: 4px; cursor: pointer; color: #1a0f08; margin: 0 2px; transition: opacity var(--transition); min-height: 32px; }
.btn-sm.blue { background: var(--accent-primary); }
.btn-sm.gold { background: #b88626; }
.btn-sm.red { background: #a83838; color: #fff; }
.btn-sm:hover { opacity: 0.8; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 14; backdrop-filter: blur(2px); }
.sidebar-overlay.open { display: block; }
@media (max-width: 768px) {
    body { flex-direction: column; }
    .hamburger { display: block; }
    .sidebar { position: fixed; top: 0; left: 0; bottom: 0; width: 280px; transform: translateX(-100%); z-index: 15; border-right: 1px solid var(--border-light); box-shadow: var(--shadow-panel); }
    .sidebar.open { transform: translateX(0); }
    .main-content { padding: 1rem; margin-top: 3rem; }
}
</style>
<script>
    (function(){
        const t=localStorage.getItem('ui-theme')||'dark';
        const c=localStorage.getItem('ui-color')||'warm';
        document.documentElement.setAttribute('data-theme', t);
        document.documentElement.setAttribute('data-theme-color', c);
    })();
    function toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('open');
        document.querySelector('.sidebar-overlay').classList.toggle('open');
    }
    function closeSidebar() {
        document.querySelector('.sidebar').classList.remove('open');
        document.querySelector('.sidebar-overlay').classList.remove('open');
    }
    function renameTag(oldTag) {
        const newTag = prompt('重命名标签 "' + oldTag + '" 为：');
        if (!newTag || newTag === oldTag) return;
        fetch('/api/v1/tags/rename', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old: oldTag, new: newTag })
        })
        .then(r => r.json())
        .then(data => { alert(data.message || '成功'); location.reload(); })
        .catch(() => alert('操作失败'));
    }
    function deleteTag(tag) {
        if (!confirm('确认删除标签 "' + tag + '" ？')) return;
        fetch('/api/v1/tags/' + encodeURIComponent(tag), { method: 'DELETE' })
        .then(r => r.json())
        .then(data => { alert(data.message || '成功'); location.reload(); })
        .catch(() => alert('操作失败'));
    }
    function mergeTag(source) {
        const target = prompt('合并标签 "' + source + '" 到目标标签：');
        if (!target || target === source) return;
        fetch('/api/v1/tags/merge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: source, target: target })
        })
        .then(r => r.json())
        .then(data => { alert(data.message || '成功'); location.reload(); })
        .catch(() => alert('操作失败'));
    }
</script>
</head>
<body>
    <button class="hamburger" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    <div class="sidebar">
        <div class="logo"><i class="fas fa-cubes"></i> 应用加载器</div>
        <nav>
            <a href="/admin/dashboard"><i class="fas fa-chart-pie"></i> 总览</a>
            <a href="/admin/apps"><i class="fas fa-th"></i> 应用管理</a>
            <a href="/admin/logs"><i class="fas fa-history"></i> 访问日志</a>
            <a href="/admin/audit"><i class="fas fa-clipboard-list"></i> 审计日志</a>
            <a href="/admin/health"><i class="fas fa-heartbeat"></i> 健康检查</a>
            <a href="/admin/versions"><i class="fas fa-code-branch"></i> 版本管理</a>
            <a href="/admin/tags" class="active"><i class="fas fa-tags"></i> 标签管理</a>
            <a href="/admin/settings"><i class="fas fa-sliders-h"></i> 设置</a>
            <a href="/api/v1/license/quota-page"><i class="fas fa-key"></i> 授权状态</a>
            <a href="/admin/change-password"><i class="fas fa-key"></i> 修改密码</a>
            <a href="/admin/users"><i class="fas fa-users"></i> 用户管理</a>
            <a href="/"><i class="fas fa-home"></i> 首页</a>
        </nav>
        <div class="user-info"><i class="fas fa-user"></i> {{ session.get('user') }} (管理员)</div>
    </div>
    <div class="main-content">
        <div class="page-title"><i class="fas fa-tags"></i> 标签管理</div>
        <div class="section">
            <div class="responsive-table">
                <table>
                    <thead><tr><th>标签名</th><th>使用次数</th><th>操作</th></tr></thead>
                    <tbody>
                    {% for tag, count in tags.items()|sort(attribute='1', reverse=true) %}
                    <tr>
                        <td>{{ tag }}</td>
                        <td>{{ count }}</td>
                        <td>
                            <button class="btn-sm blue" onclick="renameTag('{{ tag }}')"><i class="fas fa-edit"></i> 重命名</button>
                            <button class="btn-sm gold" onclick="mergeTag('{{ tag }}')"><i class="fas fa-compress"></i> 合并</button>
                            <button class="btn-sm red" onclick="deleteTag('{{ tag }}')"><i class="fas fa-trash"></i> 删除</button>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="3" class="placeholder-text">暂无标签</td></tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''