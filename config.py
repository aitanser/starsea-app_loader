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
USER_HISTORY_PATH = os.path.join(DATA_DIR, 'user_history.json')   # 新增

os.makedirs(DEFAULT_APPS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'logs'), exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, 'backups'), exist_ok=True)