@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=python
where python >nul 2>&1
if %errorlevel%==0 goto found
set PY=py
where py >nul 2>&1
if %errorlevel%==0 goto found
echo 未找到 Python，请先安装 Python 3 并勾选 "Add Python to PATH"。
pause
exit /b
:found
echo 使用 %PY% 启动任务工作台（端口 8765）。
echo 启动后自动打开浏览器。关闭本窗口即停止服务。
echo.
%PY% server.py
pause
