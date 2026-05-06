#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

export TZB_BACKEND_ENTRY_LABEL="三端统一"
export PORT="8000"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "错误: 未找到统一后端目录 $BACKEND_DIR"
    exit 1
fi

echo "========================================="
echo "启动三端共用统一后端"
echo "========================================="
echo "后端目录: $BACKEND_DIR"
echo "API 地址: http://127.0.0.1:8000"
echo "API 文档: http://127.0.0.1:8000/docs"
echo "患者端小程序接口: http://127.0.0.1:8000/api/patient"
echo "医生端 Web 接口: http://127.0.0.1:8000/api/doctor"
echo "管理端 Web 接口: http://127.0.0.1:8000/api/admin"
echo "========================================="

exec bash "$BACKEND_DIR/start.sh" "$@"
