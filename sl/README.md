# 智能手表 BLE 接入文档

本文档目录记录自研智能手表通过 BLE 接入患者端小程序，并上传血压、心率等健康数据的方案。

## 文档列表

- [BLE 协议定义](./ble-smartwatch-protocol.md)
- [固件对接说明](./ble-smartwatch-firmware-guide.md)
- [小程序联调与排障](./ble-smartwatch-miniprogram-test.md)

## 当前实现范围

- 已复用患者端小程序 `pages/device/device` 作为智能手表连接页。
- 已定义手表 BLE Service 和 Characteristic UUID。
- 已实现小程序端扫描、连接、服务发现、特征发现、通知订阅。
- 已实现手表 JSON 数据解析和 BLE 分包拼接。
- 已复用现有 `patientApi.createMeasurement` 上传血压和心率。
- 已修正首页分别读取最新血压和最新心率，避免心率记录被误当成血压。

## 相关代码

- `frontend/patient/pages/device/device.js`
- `frontend/patient/pages/device/device.wxml`
- `frontend/patient/pages/device/device.wxss`
- `frontend/patient/pages/device/device.json`
- `frontend/patient/pages/index/index.js`
- `frontend/patient/app.json`
- `frontend/patient/pages/mine/mine.wxml`

## 后续硬件联调顺序

1. 固件广播设备名使用 `TZB-WATCH-001` 或其他 `TZB-WATCH` 前缀名称。
2. 固件创建文档中定义的 BLE Service 和 Notify/Write Characteristic。
3. 固件通过 Notify Characteristic 发送换行结尾的 UTF-8 JSON。
4. 小程序进入 `设备同步` 页面，点击 `搜索手表`。
5. 连接设备后等待手表上报，或点击 `触发测量`。
6. 小程序收到数据后自动上传到后端监测数据接口。

## 注意事项

- 真机联调需要手机蓝牙开启。
- 微信开发者工具对 BLE 能力支持有限，最终需要真机调试。
- 小程序后台隐私协议和权限声明需要包含蓝牙相关用途。
- 血压数据如果来自算法估算，后续产品和医疗风险说明需要单独确认。
