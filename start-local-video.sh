#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
SRS_DOMAIN="${SRS_DOMAIN:-}"
SRS_HOST="${SRS_HOST:-${LOCAL_IP:-$SRS_DOMAIN}}"
SRS_HOST="${SRS_HOST:-${LOCAL_IP:-127.0.0.1}}"
export SRS_CANDIDATE="${SRS_CANDIDATE:-$SRS_HOST}"

if docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker-compose)
else
  echo "未找到 docker compose，请先安装 Docker 和 Docker Compose。" >&2
  exit 1
fi

"${DOCKER_COMPOSE[@]}" -f "$ROOT_DIR/docker-compose.srs.yml" up -d

cat <<EOF

本地 SRS 音视频服务已启动。

请把 /root/tzb/backend/.env 配置为：
VIDEO_PUSH_BASE_URL=webrtc://$SRS_HOST/live
VIDEO_PLAY_BASE_URL=webrtc://$SRS_HOST/live
VIDEO_RTC_API_BASE_URL=http://$SRS_HOST:1985

当前本机局域网 IP：${LOCAL_IP:-未检测到}
患者小程序真机请连接同一局域网，并确保手机能访问 $SRS_HOST。
医生端本机浏览器建议使用 http://localhost:5173/doctor/consultations 打开，以便浏览器允许摄像头/麦克风权限。

EOF
