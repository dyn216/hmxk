@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:menu
cls
echo =========================================
echo    慢性病管理系统 - 后端一键部署工具
echo =========================================
echo.
echo 请选择操作：
echo.
echo   1. 完整部署（首次安装）
echo   2. 启动服务
echo   3. 停止服务
echo   4. 重启服务
echo   5. 更新依赖
echo   6. 重置数据库
echo   7. 查看服务状态
echo   8. 查看日志
echo   9. 卸载环境
echo   0. 退出
echo.
echo =========================================
set /p choice=请输入选项 (0-9): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto update_deps
if "%choice%"=="6" goto reset_db
if "%choice%"=="7" goto status
if "%choice%"=="8" goto logs
if "%choice%"=="9" goto uninstall
if "%choice%"=="0" goto end
echo 无效选项，请重新选择
pause
goto menu

:install
cls
echo =========================================
echo 开始完整部署...
echo =========================================
echo.

REM 检查Python
echo [1/6] 检查Python环境...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    goto menu
)

python --version
echo [✓] Python环境正常
echo.

REM 创建虚拟环境
echo [2/6] 创建虚拟环境...
if exist "venv" (
    echo [提示] 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] 创建虚拟环境失败
        pause
        goto menu
    )
    echo [✓] 虚拟环境创建成功
)
echo.

REM 激活虚拟环境
echo [3/6] 激活虚拟环境...
call venv\Scripts\activate.bat
echo [✓] 虚拟环境已激活
echo.

REM 升级pip
echo [4/6] 升级pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 安装依赖
echo [5/6] 安装依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 依赖安装失败
    pause
    goto menu
)
echo [✓] 依赖安装成功
echo.

REM 初始化数据库
echo [6/6] 初始化数据库...
if exist "chronic_disease.db" (
    echo [提示] 数据库已存在，如需重置请选择菜单选项6
) else (
    python init_db.py
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] 数据库初始化失败
        pause
        goto menu
    )
    echo [✓] 数据库初始化成功
)
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

echo =========================================
echo 部署完成！
echo =========================================
echo.
echo 测试账号：
echo   管理员：13800000000 / admin123
echo   医生：  13800000001 / doctor123
echo   患者：  13900000001 / patient123
echo.
echo 现在可以选择菜单选项2启动服务
echo =========================================
pause
goto menu

:start
cls
echo =========================================
echo 启动后端服务...
echo =========================================
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo [错误] 虚拟环境不存在，请先执行完整部署（选项1）
    pause
    goto menu
)

REM 检查端口占用
netstat -ano | findstr ":8000" >nul
if %ERRORLEVEL% EQU 0 (
    echo [警告] 端口8000已被占用
    echo 请先停止现有服务（选项3）或检查端口占用
    pause
    goto menu
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 健康检查: http://localhost:8000/health
echo.
echo 按 Ctrl+C 停止服务
echo =========================================
echo.

REM 启动服务
start /B uvicorn main:app --host 0.0.0.0 --port 8000 > logs\server.log 2>&1

REM 等待服务启动
timeout /t 3 /nobreak >nul

REM 检查服务是否启动成功
netstat -ano | findstr ":8000" >nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] 服务启动成功
    echo.
    echo 你可以：
    echo - 浏览器访问: http://localhost:8000/docs
    echo - 返回菜单继续其他操作
) else (
    echo [错误] 服务启动失败，请查看日志
    echo 日志文件: logs\server.log
)
echo.
pause
goto menu

:stop
cls
echo =========================================
echo 停止后端服务...
echo =========================================
echo.

REM 查找进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    echo 找到进程 PID: %%a
    taskkill /PID %%a /F >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [✓] 服务已停止
    ) else (
        echo [警告] 停止进程失败，可能需要管理员权限
    )
)

REM 检查是否还有进程
netstat -ano | findstr ":8000" >nul
if %ERRORLEVEL% EQU 0 (
    echo [警告] 端口仍被占用，请手动检查
) else (
    echo [✓] 端口8000已释放
)

echo.
pause
goto menu

:restart
cls
echo =========================================
echo 重启后端服务...
echo =========================================
echo.

REM 先停止
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /PID %%a /F >nul 2>nul
)

echo 等待服务停止...
timeout /t 2 /nobreak >nul

REM 再启动
if not exist "venv" (
    echo [错误] 虚拟环境不存在
    pause
    goto menu
)

call venv\Scripts\activate.bat
echo 正在重启服务...
start /B uvicorn main:app --host 0.0.0.0 --port 8000 > logs\server.log 2>&1

timeout /t 3 /nobreak >nul

netstat -ano | findstr ":8000" >nul
if %ERRORLEVEL% EQU 0 (
    echo [✓] 服务重启成功
    echo 访问地址: http://localhost:8000
) else (
    echo [错误] 服务启动失败
)

echo.
pause
goto menu

:update_deps
cls
echo =========================================
echo 更新依赖包...
echo =========================================
echo.

if not exist "venv" (
    echo [错误] 虚拟环境不存在
    pause
    goto menu
)

call venv\Scripts\activate.bat
pip install -r requirements.txt --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [✓] 依赖更新完成
pause
goto menu

:reset_db
cls
echo =========================================
echo 重置数据库
echo =========================================
echo.
echo [警告] 此操作将删除所有数据！
echo.
set /p confirm=确认重置数据库吗？(Y/N): 

if /i not "%confirm%"=="Y" (
    echo 操作已取消
    pause
    goto menu
)

if exist "chronic_disease.db" (
    del chronic_disease.db
    echo [✓] 旧数据库已删除
)

if not exist "venv" (
    echo [错误] 虚拟环境不存在
    pause
    goto menu
)

call venv\Scripts\activate.bat
python init_db.py

if %ERRORLEVEL% EQU 0 (
    echo [✓] 数据库重置成功
) else (
    echo [错误] 数据库初始化失败
)

echo.
pause
goto menu

:status
cls
echo =========================================
echo 服务状态
echo =========================================
echo.

REM 检查进程
netstat -ano | findstr ":8000" >nul
if %ERRORLEVEL% EQU 0 (
    echo [运行中] 服务正在运行
    echo.
    echo 端口信息：
    netstat -ano | findstr ":8000"
    echo.
    echo 访问地址:
    echo - 主页: http://localhost:8000
    echo - API文档: http://localhost:8000/docs
    echo - 健康检查: http://localhost:8000/health
) else (
    echo [已停止] 服务未运行
)

echo.
echo 环境信息：
if exist "venv" (
    echo [✓] 虚拟环境：已创建
) else (
    echo [✗] 虚拟环境：未创建
)

if exist "chronic_disease.db" (
    echo [✓] 数据库：已初始化
) else (
    echo [✗] 数据库：未初始化
)

if exist "logs" (
    echo [✓] 日志目录：已创建
) else (
    echo [✗] 日志目录：未创建
)

echo.
pause
goto menu

:logs
cls
echo =========================================
echo 查看日志（最后50行）
echo =========================================
echo.

if exist "logs\server.log" (
    powershell -command "Get-Content logs\server.log -Tail 50"
) else (
    echo 日志文件不存在
)

if exist "logs\app.log" (
    echo.
    echo --- 应用日志 ---
    powershell -command "Get-Content logs\app.log -Tail 20"
)

echo.
pause
goto menu

:uninstall
cls
echo =========================================
echo 卸载环境
echo =========================================
echo.
echo [警告] 此操作将删除：
echo - 虚拟环境
echo - 数据库
echo - 日志文件
echo.
set /p confirm=确认卸载吗？(Y/N): 

if /i not "%confirm%"=="Y" (
    echo 操作已取消
    pause
    goto menu
)

REM 停止服务
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /PID %%a /F >nul 2>nul
)

REM 删除虚拟环境
if exist "venv" (
    rmdir /s /q venv
    echo [✓] 虚拟环境已删除
)

REM 删除数据库
if exist "chronic_disease.db" (
    del chronic_disease.db
    echo [✓] 数据库已删除
)

REM 删除日志
if exist "logs" (
    rmdir /s /q logs
    echo [✓] 日志已删除
)

echo.
echo [✓] 卸载完成
pause
goto menu

:end
echo.
echo 感谢使用！
exit /b 0
