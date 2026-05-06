#!/bin/bash

# 慢性病管理系统 - 后端一键部署工具

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PORT=8000
LOG_DIR="logs"
DB_FILE="chronic_disease.db"
VENV_DIR="venv"

# 显示菜单
show_menu() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}   慢性病管理系统 - 后端一键部署工具${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo "请选择操作："
    echo ""
    echo "  1. 完整部署（首次安装）"
    echo "  2. 启动服务"
    echo "  3. 停止服务"
    echo "  4. 重启服务"
    echo "  5. 更新依赖"
    echo "  6. 重置数据库"
    echo "  7. 查看服务状态"
    echo "  8. 查看日志"
    echo "  9. 卸载环境"
    echo "  0. 退出"
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    read -p "请输入选项 (0-9): " choice
    
    case $choice in
        1) install ;;
        2) start_service ;;
        3) stop_service ;;
        4) restart_service ;;
        5) update_deps ;;
        6) reset_db ;;
        7) show_status ;;
        8) show_logs ;;
        9) uninstall ;;
        0) exit 0 ;;
        *) echo -e "${RED}无效选项，请重新选择${NC}" ; sleep 2 ; show_menu ;;
    esac
}

# 完整部署
install() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}开始完整部署...${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    # 检查Python
    echo -e "${YELLOW}[1/6] 检查Python环境...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[错误] 未找到Python3，请先安装Python 3.8+${NC}"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    python3 --version
    echo -e "${GREEN}[✓] Python环境正常${NC}"
    echo ""
    
    # 创建虚拟环境
    echo -e "${YELLOW}[2/6] 创建虚拟环境...${NC}"
    if [ -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}[提示] 虚拟环境已存在，跳过创建${NC}"
    else
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            echo -e "${RED}[错误] 创建虚拟环境失败${NC}"
            read -p "按回车返回菜单..."
            show_menu
            return
        fi
        echo -e "${GREEN}[✓] 虚拟环境创建成功${NC}"
    fi
    echo ""
    
    # 激活虚拟环境
    echo -e "${YELLOW}[3/6] 激活虚拟环境...${NC}"
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}[✓] 虚拟环境已激活${NC}"
    echo ""
    
    # 升级pip
    echo -e "${YELLOW}[4/6] 升级pip...${NC}"
    pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo ""
    
    # 安装依赖
    echo -e "${YELLOW}[5/6] 安装依赖包...${NC}"
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误] 依赖安装失败${NC}"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    echo -e "${GREEN}[✓] 依赖安装成功${NC}"
    echo ""
    
    # 初始化数据库
    echo -e "${YELLOW}[6/6] 初始化数据库...${NC}"
    if [ -f "$DB_FILE" ]; then
        echo -e "${YELLOW}[提示] 数据库已存在，如需重置请选择菜单选项6${NC}"
    else
        python3 init_db.py
        if [ $? -ne 0 ]; then
            echo -e "${RED}[错误] 数据库初始化失败${NC}"
            read -p "按回车返回菜单..."
            show_menu
            return
        fi
        echo -e "${GREEN}[✓] 数据库初始化成功${NC}"
    fi
    echo ""
    
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${GREEN}部署完成！${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo "测试账号："
    echo "  管理员：13800000000 / admin123"
    echo "  医生：  13800000001 / doctor123"
    echo "  患者：  13900000001 / patient123"
    echo ""
    echo "现在可以选择菜单选项2启动服务"
    echo -e "${BLUE}=========================================${NC}"
    
    read -p "按回车返回菜单..."
    show_menu
}

# 启动服务
start_service() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}启动后端服务...${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    # 检查虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}[错误] 虚拟环境不存在，请先执行完整部署（选项1）${NC}"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    
    # 检查端口占用
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}[警告] 端口${PORT}已被占用${NC}"
        echo "请先停止现有服务（选项3）或检查端口占用"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    echo "访问地址: http://localhost:$PORT"
    echo "API文档: http://localhost:$PORT/docs"
    echo "健康检查: http://localhost:$PORT/health"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    # 启动服务
    nohup uvicorn main:app --host 0.0.0.0 --port $PORT > "$LOG_DIR/server.log" 2>&1 &
    
    # 记录PID
    echo $! > "$LOG_DIR/server.pid"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否启动成功
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}[✓] 服务启动成功${NC}"
        echo ""
        echo "你可以："
        echo "- 浏览器访问: http://localhost:$PORT/docs"
        echo "- 返回菜单继续其他操作"
    else
        echo -e "${RED}[错误] 服务启动失败，请查看日志${NC}"
        echo "日志文件: $LOG_DIR/server.log"
    fi
    
    echo ""
    read -p "按回车返回菜单..."
    show_menu
}

# 停止服务
stop_service() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}停止后端服务...${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    # 查找并停止进程
    if [ -f "$LOG_DIR/server.pid" ]; then
        PID=$(cat "$LOG_DIR/server.pid")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo -e "${GREEN}[✓] 服务已停止 (PID: $PID)${NC}"
            rm "$LOG_DIR/server.pid"
        else
            echo -e "${YELLOW}[提示] PID文件存在但进程不存在${NC}"
            rm "$LOG_DIR/server.pid"
        fi
    fi
    
    # 通过端口查找进程
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        kill $PID
        echo -e "${GREEN}[✓] 停止了端口${PORT}上的进程 (PID: $PID)${NC}"
    fi
    
    # 检查是否还有进程
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}[警告] 端口仍被占用，请手动检查${NC}"
    else
        echo -e "${GREEN}[✓] 端口${PORT}已释放${NC}"
    fi
    
    echo ""
    read -p "按回车返回菜单..."
    show_menu
}

# 重启服务
restart_service() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}重启后端服务...${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    # 先停止
    if [ -f "$LOG_DIR/server.pid" ]; then
        PID=$(cat "$LOG_DIR/server.pid")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            rm "$LOG_DIR/server.pid"
        fi
    fi
    
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        kill $PID
    fi
    
    echo "等待服务停止..."
    sleep 2
    
    # 再启动
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}[错误] 虚拟环境不存在${NC}"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    
    source "$VENV_DIR/bin/activate"
    echo "正在重启服务..."
    nohup uvicorn main:app --host 0.0.0.0 --port $PORT > "$LOG_DIR/server.log" 2>&1 &
    echo $! > "$LOG_DIR/server.pid"
    
    sleep 3
    
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}[✓] 服务重启成功${NC}"
        echo "访问地址: http://localhost:$PORT"
    else
        echo -e "${RED}[错误] 服务启动失败${NC}"
    fi
    
    echo ""
    read -p "按回车返回菜单..."
    show_menu
}

# 更新依赖
update_deps() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}更新依赖包...${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}[错误] 虚拟环境不存在${NC}"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    echo ""
    echo -e "${GREEN}[✓] 依赖更新完成${NC}"
    
    read -p "按回车返回菜单..."
    show_menu
}

# 重置数据库
reset_db() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}重置数据库${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo -e "${RED}[警告] 此操作将删除所有数据！${NC}"
    echo ""
    read -p "确认重置数据库吗？(y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "操作已取消"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    
    if [ -f "$DB_FILE" ]; then
        rm "$DB_FILE"
        echo -e "${GREEN}[✓] 旧数据库已删除${NC}"
    fi
    
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}[错误] 虚拟环境不存在${NC}"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    
    source "$VENV_DIR/bin/activate"
    python3 init_db.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[✓] 数据库重置成功${NC}"
    else
        echo -e "${RED}[错误] 数据库初始化失败${NC}"
    fi
    
    echo ""
    read -p "按回车返回菜单..."
    show_menu
}

# 查看状态
show_status() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}服务状态${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    # 检查进程
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}[运行中] 服务正在运行${NC}"
        echo ""
        echo "进程信息："
        lsof -Pi :$PORT -sTCP:LISTEN
        echo ""
        echo "访问地址:"
        echo "- 主页: http://localhost:$PORT"
        echo "- API文档: http://localhost:$PORT/docs"
        echo "- 健康检查: http://localhost:$PORT/health"
    else
        echo -e "${YELLOW}[已停止] 服务未运行${NC}"
    fi
    
    echo ""
    echo "环境信息："
    
    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}[✓] 虚拟环境：已创建${NC}"
    else
        echo -e "${RED}[✗] 虚拟环境：未创建${NC}"
    fi
    
    if [ -f "$DB_FILE" ]; then
        echo -e "${GREEN}[✓] 数据库：已初始化${NC}"
    else
        echo -e "${RED}[✗] 数据库：未初始化${NC}"
    fi
    
    if [ -d "$LOG_DIR" ]; then
        echo -e "${GREEN}[✓] 日志目录：已创建${NC}"
    else
        echo -e "${RED}[✗] 日志目录：未创建${NC}"
    fi
    
    echo ""
    read -p "按回车返回菜单..."
    show_menu
}

# 查看日志
show_logs() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}查看日志（最后50行）${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    if [ -f "$LOG_DIR/server.log" ]; then
        tail -n 50 "$LOG_DIR/server.log"
    else
        echo "日志文件不存在"
    fi
    
    if [ -f "$LOG_DIR/app.log" ]; then
        echo ""
        echo "--- 应用日志 ---"
        tail -n 20 "$LOG_DIR/app.log"
    fi
    
    echo ""
    read -p "按回车返回菜单..."
    show_menu
}

# 卸载环境
uninstall() {
    clear
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}卸载环境${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    echo -e "${RED}[警告] 此操作将删除：${NC}"
    echo "- 虚拟环境"
    echo "- 数据库"
    echo "- 日志文件"
    echo ""
    read -p "确认卸载吗？(y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "操作已取消"
        read -p "按回车返回菜单..."
        show_menu
        return
    fi
    
    # 停止服务
    if [ -f "$LOG_DIR/server.pid" ]; then
        PID=$(cat "$LOG_DIR/server.pid")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
        fi
    fi
    
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        kill $PID
    fi
    
    # 删除虚拟环境
    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
        echo -e "${GREEN}[✓] 虚拟环境已删除${NC}"
    fi
    
    # 删除数据库
    if [ -f "$DB_FILE" ]; then
        rm "$DB_FILE"
        echo -e "${GREEN}[✓] 数据库已删除${NC}"
    fi
    
    # 删除日志
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        echo -e "${GREEN}[✓] 日志已删除${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}[✓] 卸载完成${NC}"
    
    read -p "按回车返回菜单..."
    show_menu
}

# 主程序
main() {
    # 检查是否在backend目录
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}错误: 请在backend目录下运行此脚本${NC}"
        exit 1
    fi
    
    show_menu
}

# 运行主程序
main
