#!/usr/bin/env python3
# config.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

import os

DEFAULT_PORT = 8000
DEFAULT_APPS_DIR = os.path.join(os.getcwd(), 'apps')
DATA_DIR = os.path.join(os.getcwd(), 'data')
ADMIN_CONFIG_PATH = os.path.join(DATA_DIR, 'admin_config.json')
CONFIG_PATH = os.path.join(DATA_DIR, 'framework_config.json')
LOG_PATH = os.path.join(DATA_DIR, 'logs', 'access.log')
APP_CONFIG_PATH = os.path.join(DATA_DIR, 'apps_config.json')
FAVORITES_PATH = os.path.join(DATA_DIR, 'favorites.json')
NOTE_PATH = os.path.join(DATA_DIR, 'notes.json')
USER_HISTORY_PATH = os.path.join(DATA_DIR, 'user_history.json')

# ===== 授权配置 =====
LOADER_LICENSE_PATH = os.environ.get('LOADER_LICENSE_PATH', os.path.join(DATA_DIR, 'loader.lic'))
LOADER_SECRET_KEY = os.environ.get('LOADER_SECRET_KEY', 'change-me-in-production')
LOADER_ENABLED = os.environ.get('LOADER_ENABLED', 'true').lower() == 'true'

# ===== 激活码哈希库 =====
ACTIVATION_KEYS_FILE = os.environ.get(
    'LOADER_ACTIVATION_KEYS_FILE',
    os.path.join(DATA_DIR, 'activation_keys.json')
)

# ===== 登录失败限制 =====
LOGIN_FAIL_FILE = os.path.join(DATA_DIR, 'login_fails.json')

# 创建必要目录
os.makedirs(DEFAULT_APPS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'logs'), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'backups'), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'screenshots'), exist_ok=True)