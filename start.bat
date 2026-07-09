@echo off
chcp 65001 >nul

echo ========================================
echo   万能应用加载器
echo ========================================
echo.

REM ---------- 检查 Python ----------
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.6+
    pause
    exit /b 1
)

REM ---------- 创建必要目录 ----------
if not exist "data" mkdir data
if not exist "data\logs" mkdir data\logs
if not exist "data\screenshots" mkdir data\screenshots
if not exist "data\backups" mkdir data\backups
if not exist "apps" mkdir apps
echo [目录] 必要目录已创建
echo.

REM ---------- 检查并安装依赖 ----------
echo [依赖] 检查依赖...

python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [依赖] 首次运行，正在安装依赖...
    pip install -r requirements.txt
    echo.
)

python -c "import bcrypt" >nul 2>&1
if errorlevel 1 (
    echo [依赖] 安装 bcrypt...
    pip install bcrypt
    echo.
)

python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo [依赖] 安装 Playwright...
    pip install playwright
    echo.
)

REM ---------- 检查 Playwright 浏览器 ----------
python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().stop()" >nul 2>&1
if errorlevel 1 (
    echo [依赖] Playwright 浏览器未安装，正在安装...
    playwright install chromium
    echo.
)

REM ---------- 检查环境变量 ----------
echo [环境] 检查环境变量...

python -c "import os; exit(0 if os.environ.get('LOADER_SECRET_KEY') and os.environ.get('LOADER_SECRET_KEY') != 'change-me-in-production' else 1)" >nul 2>&1
if errorlevel 1 (
    echo [警告] LOADER_SECRET_KEY 未设置或使用默认值
    echo   生产环境请设置: set LOADER_SECRET_KEY=your-strong-random-key
    echo.
)

REM ---------- 激活码检查 ----------
echo [激活码] 检查激活码库...
if not exist "data\activation_keys.json" (
    echo [信息] 激活码库不存在，首次启动将自动创建
    echo   使用 python generate_loader_activation.py 生成激活码
    echo.
)

REM ---------- 启动服务 ----------
echo [启动] 启动加载器服务...
echo.

if "%1"=="--no-pause" (
    python app.py %*
) else (
    python app.py %*
    pause
)