#!/bin/bash
# 万能应用加载器启动脚本

echo "========================================"
echo "  万能应用加载器"
echo "========================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.6+"
    exit 1
fi

python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "首次运行，正在安装依赖..."
    pip3 install -r requirements.txt
    echo ""
fi

python3 app.py "$@"