@echo off
chcp 65001 
echo ========================================
echo   万能应用加载器
echo ========================================
echo.

python --version  2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.6+
    pause
    exit /b 1
)

python -c "import flask"  2>&1
if errorlevel 1 (
    echo 首次运行，正在安装依赖...
    pip install -r requirements.txt
    echo.
)

python app.py %*
pause