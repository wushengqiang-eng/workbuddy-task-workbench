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
echo 使用 %PY% 启动【科技版】任务工作台（端口 8766）。
echo 可与普通版同时运行。关闭本窗口即停止。
echo.
%PY% server-tech.py
pause
