#!/bin/bash
# ============================================================
# 万能应用加载器 启动脚本（Linux/macOS）
# ============================================================

set -e

echo "========================================"
echo "  万能应用加载器"
echo "========================================"
echo ""

# ---------- 检查 Python ----------
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.6+"
    exit 1
fi

# ---------- 创建必要目录 ----------
mkdir -p data data/logs data/screenshots data/backups apps
echo "📁 必要目录已创建"
echo ""

# ---------- 检测 pip ----------
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    if command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        echo "❌ 错误: 未找到 pip，请安装 pip"
        exit 1
    fi
fi

# ---------- 检查并安装依赖 ----------
echo "📦 检查依赖..."

if ! python3 -c "import flask" 2>/dev/null; then
    echo "   首次运行，正在安装依赖..."
    $PIP_CMD install -r requirements.txt
    echo ""
fi

if ! python3 -c "import bcrypt" 2>/dev/null; then
    echo "   安装 bcrypt..."
    $PIP_CMD install bcrypt
    echo ""
fi

if ! python3 -c "import playwright" 2>/dev/null; then
    echo "   安装 Playwright..."
    $PIP_CMD install playwright
    echo ""
fi

# ---------- 检查 Playwright 浏览器 ----------
if ! python3 -c "from playwright.sync_api import sync_playwright; sync_playwright().start().stop()" 2>/dev/null; then
    echo "   Playwright 浏览器未安装，正在安装..."
    playwright install chromium
    echo ""
fi

# ---------- 检查环境变量 ----------
echo "🔑 检查环境变量..."

if [ -z "$LOADER_SECRET_KEY" ] || [ "$LOADER_SECRET_KEY" = "change-me-in-production" ]; then
    echo "   ⚠️  警告: LOADER_SECRET_KEY 未设置或使用默认值"
    echo "   生产环境请设置: export LOADER_SECRET_KEY=\"your-strong-random-key\""
    echo ""
fi

# ---------- 激活码检查 ----------
echo "📋 检查激活码库..."
if [ ! -f "data/activation_keys.json" ]; then
    echo "   ℹ️  激活码库不存在，首次启动将自动创建"
    echo "   使用 python generate_loader_activation.py 生成激活码"
    echo ""
fi

# ---------- 启动服务 ----------
echo "🚀 启动加载器服务..."
echo ""

python3 app.py "$@"