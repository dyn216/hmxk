# 慢性病管理 Web 端

患者端继续使用 `frontend/patient` 微信小程序。

医生端和管理端统一使用本目录的 Vue Web 工作台：

- 医生端：`/doctor`
- 管理端：`/admin`
- 医生端后端地址：`http://127.0.0.1:8012`
- 管理端后端地址：`http://127.0.0.1:8013`

## 启动方式

先安装依赖：

```powershell
npm install
```

启动 Vue 开发服务器：

```powershell
npm run dev
```

然后访问：

- `http://127.0.0.1:5173/doctor`
- `http://127.0.0.1:5173/admin`

## 目录说明

- `index.html`：Web 应用入口
- `vite.config.js`：Vue/Vite 开发服务器配置
- `src/main.js`：Vue 应用入口
- `src/App.vue`：医生端和管理端页面
- `src/config.js`：医生端与管理端 API 地址配置
- `src/styles.css`：统一布局与视觉样式
