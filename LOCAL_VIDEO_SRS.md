# 本地 SRS 音视频问诊

本方案用于本地跑通患者小程序与医生 Web 的视频 + 音频问诊。

## 1. 启动本地 SRS

```bash
bash /root/tzb/start-local-video.sh
```

脚本会启动 `docker-compose.srs.yml` 中的 `tzb-local-srs` 容器，并打印应该写入后端 `.env` 的配置。

默认使用当前项目域名的 RTC 子域名：

```text
rtc.yun-an.xyz
```

## 2. 后端视频配置

`/root/tzb/backend/.env` 需要包含：

```env
VIDEO_PUSH_BASE_URL=webrtc://rtc.yun-an.xyz/live
VIDEO_PLAY_BASE_URL=webrtc://rtc.yun-an.xyz/live
VIDEO_RTC_API_BASE_URL=http://rtc.yun-an.xyz:1985
```

当前已按 RTC 子域名写入：

```env
VIDEO_PUSH_BASE_URL=webrtc://rtc.yun-an.xyz/live
VIDEO_PLAY_BASE_URL=webrtc://rtc.yun-an.xyz/live
VIDEO_RTC_API_BASE_URL=http://rtc.yun-an.xyz:1985
```

修改 `.env` 后需要重启 FastAPI 后端。

## 3. DNS 配置

`rtc.yun-an.xyz` 需要解析到 SRS 所在机器可被访问的地址。

局域网测试可以用：

```text
rtc.yun-an.xyz -> 10.12.28.32
```

公网测试需要用：

```text
rtc.yun-an.xyz -> 服务器公网 IP
```

Cloudflare 上这条记录必须设置为 **DNS only / 灰云**，不要开启代理；Cloudflare Tunnel 只能代理 HTTP，不能代理 SRS WebRTC 的 `8000/udp` 媒体流。

## 4. 端口要求

本地 SRS 会使用：

- `1935/tcp` RTMP
- `1985/tcp` SRS HTTP API
- `8080/tcp` SRS HTTP Server
- `8000/udp` WebRTC UDP

请确保手机和医生端电脑能访问这些端口。

## 5. 使用方式

1. 启动 SRS。
2. 重启后端。
3. 启动医生端前端。
4. 患者端小程序发起视频问诊。
5. 医生端在问诊列表点击“加入视频”。
6. 医生端点击“开启摄像头/麦克风”。
7. 患者端进入视频页后会通过 `live-pusher/live-player` 推送和播放音视频。

## 6. 注意事项

- 患者真机不能使用 `localhost`，必须使用可访问的局域网 IP 或解析正确的域名。
- `rtc.yun-an.xyz` 不要通过 Cloudflare Tunnel 作为 WebRTC 媒体入口，除非额外使用支持 UDP/TURN/Spectrum 的方案。
- 医生端如果用浏览器本地测试，建议打开 `http://localhost:5173/doctor/consultations`，浏览器才会允许摄像头/麦克风权限。
- 如果医生端通过 HTTPS 域名打开，浏览器可能阻止访问本地 `http://rtc.yun-an.xyz:1985` 的 SRS API。
- 这套本地方案适合开发测试；正式上线建议接腾讯 TRTC、声网或部署带 HTTPS/TURN 的生产级 RTC 服务。
