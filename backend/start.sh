#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_ONLY="${1:-}"

cd "$SCRIPT_DIR"

echo "========================================="
echo "慢性病管理小程序后端启动脚本"
echo "========================================="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

if [ "$CHECK_ONLY" != "--check" ]; then
    if [ ! -x "venv/bin/python" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi

    echo "激活虚拟环境..."
    source "venv/bin/activate"

    echo "检查并安装依赖包..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

    if [ ! -f "chronic_disease.db" ]; then
        echo "初始化数据库..."
        python init_db.py
    fi
else
    if [ -f "venv/bin/activate" ]; then
        source "venv/bin/activate"
    fi
fi

echo "检查后端应用..."
if [ "$CHECK_ONLY" = "--check" ]; then
    python start_backend.py --check
    exit 0
fi

python start_backend.py
