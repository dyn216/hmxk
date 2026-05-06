#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCTOR_FRONTEND="$ROOT_DIR/doctor/frontend"
ADMIN_FRONTEND="$ROOT_DIR/admin/frontend"
DOCTOR_PID=""
ADMIN_PID=""

cleanup() {
    if [ -n "${DOCTOR_PID:-}" ] && kill -0 "$DOCTOR_PID" >/dev/null 2>&1; then
        kill "$DOCTOR_PID" >/dev/null 2>&1 || true
    fi
    if [ -n "${ADMIN_PID:-}" ] && kill -0 "$ADMIN_PID" >/dev/null 2>&1; then
        kill "$ADMIN_PID" >/dev/null 2>&1 || true
    fi
}

trap cleanup EXIT INT TERM

if ! command -v npm >/dev/null 2>&1; then
    echo "错误: 未找到 npm，请先安装 Node.js 和 npm"
    exit 1
fi

if ! command -v node >/dev/null 2>&1; then
    echo "错误: 未找到 node，请先安装 Node.js"
    exit 1
fi

ensure_dependencies() {
    local app_dir="$1"
    local app_name="$2"
    if [ ! -f "$app_dir/node_modules/vite/bin/vite.js" ]; then
        echo "[$app_name] 安装前端依赖..."
        (cd "$app_dir" && npm install)
    fi
    if [ -f "$app_dir/node_modules/.bin/vite" ]; then
        chmod +x "$app_dir/node_modules/.bin/vite" || true
    fi
}

ensure_dependencies "$DOCTOR_FRONTEND" "医生端"
ensure_dependencies "$ADMIN_FRONTEND" "管理端"

echo "========================================="
echo "启动医生端和管理端 Web 前端"
echo "========================================="
echo "医生端: http://127.0.0.1:5173"
echo "管理端: http://127.0.0.1:5174"
echo "统一后端: http://127.0.0.1:8000"
echo "按 Ctrl+C 同时停止两个前端服务"
echo "========================================="

(cd "$DOCTOR_FRONTEND" && node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5173) &
DOCTOR_PID=$!

(cd "$ADMIN_FRONTEND" && node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5174) &
ADMIN_PID=$!

wait "$DOCTOR_PID" "$ADMIN_PID"
