import socket
import os
from datetime import datetime, timedelta
from config import LOG_PATH, DATA_DIR, USER_HISTORY_PATH
import json
import zipfile

# 尝试导入 chardet，若无则回退
try:
    import chardet
except ImportError:
    chardet = None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def log_access(request, app_id=None):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client = request.remote_addr
    path = request.path
    method = request.method
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {client} - {method} {path} - app:{app_id}\n')

def _safe_read_log():
    """安全读取日志文件，自动检测编码，忽略错误"""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, 'rb') as f:
        raw = f.read()
    if not raw:
        return []
    # 检测编码
    encoding = 'utf-8'
    if chardet:
        try:
            detected = chardet.detect(raw)
            if detected and detected['encoding']:
                encoding = detected['encoding']
        except:
            pass
    # 解码，忽略无法解码的字符
    try:
        text = raw.decode(encoding, errors='ignore')
    except:
        text = raw.decode('utf-8', errors='ignore')
    return text.splitlines()

def get_access_logs(lines=100):
    all_lines = _safe_read_log()
    return all_lines[-lines:] if all_lines else []

def clean_old_logs(days=30):
    lines = _safe_read_log()
    if not lines:
        return
    cutoff = datetime.now() - timedelta(days=days)
    new_lines = []
    for line in lines:
        try:
            date_str = line[1:11]
            log_date = datetime.strptime(date_str, '%Y-%m-%d')
            if log_date >= cutoff:
                new_lines.append(line)
        except:
            new_lines.append(line)
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

def get_trend_data(days=30):
    lines = _safe_read_log()
    if not lines:
        return [], []
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
    counts = {d: 0 for d in dates}
    for line in lines:
        try:
            date_str = line[1:11]
            if date_str in counts:
                counts[date_str] += 1
        except:
            pass
    return dates, [counts[d] for d in dates]

def get_recent_apps(limit=10):
    logs = get_access_logs(200)
    apps = []
    seen = set()
    for log in reversed(logs):
        if ' - app:' in log:
            app_id = log.split(' - app:')[-1].strip()
            if app_id and app_id not in seen and app_id != 'None':
                seen.add(app_id)
                apps.append(app_id)
                if len(apps) >= limit:
                    break
    return apps

def load_user_history():
    if os.path.exists(USER_HISTORY_PATH):
        with open(USER_HISTORY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_history(history):
    with open(USER_HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def record_user_app_access(username, app_id):
    if not username or username == 'anonymous':
        return
    history = load_user_history()
    if username not in history:
        history[username] = []
    if app_id in history[username]:
        history[username].remove(app_id)
    history[username].append(app_id)
    if len(history[username]) > 50:
        history[username] = history[username][-50:]
    save_user_history(history)

def safe_extract_zip(zip_file_obj, target_dir):
    abs_target = os.path.abspath(target_dir)
    os.makedirs(abs_target, exist_ok=True)
    with zipfile.ZipFile(zip_file_obj, 'r') as zf:
        for member in zf.namelist():
            if member.endswith('/'):
                continue
            member_path = os.path.abspath(os.path.join(abs_target, member))
            if not member_path.startswith(abs_target):
                raise Exception(f"检测到非法路径穿越: {member}")
        zf.extractall(abs_target)

def has_html_files(dir_path):
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            if f.lower().endswith('.html'):
                return True
    return False