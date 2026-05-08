# 智能手表小程序联调与排障

本文档说明患者端小程序智能手表页面的测试方法、数据上传验证方法和常见问题处理。

## 页面入口

### 首页入口

患者端小程序首页：

```text
设备同步
```

点击后进入：

```text
/pages/device/device
```

### 我的页入口

患者端小程序我的页：

```text
设备管理 -> 智能手表
```

同样进入：

```text
/pages/device/device
```

## 相关代码文件

```text
frontend/patient/pages/device/device.js
frontend/patient/pages/device/device.wxml
frontend/patient/pages/device/device.wxss
frontend/patient/pages/device/device.json
frontend/patient/pages/index/index.js
frontend/patient/app.json
frontend/patient/pages/mine/mine.wxml
```

## 小程序端主要流程

```text
打开页面
  -> 点击搜索手表
  -> 初始化蓝牙适配器
  -> 扫描附近 BLE 设备
  -> 过滤 TZB-WATCH 设备
  -> 点击设备连接
  -> 发现 GATT Service
  -> 发现 Notify/Write Characteristic
  -> 开启 Notify
  -> 等待手表上报 JSON
  -> 解析血压/心率
  -> 调用 /measurements 上传
```

## 未烧录固件前的测试

页面提供了：

```text
模拟一条手表数据
```

点击后会在小程序内模拟一条数据：

```json
{
  "type": "vital",
  "sys": 120,
  "dia": 80,
  "hr": 72,
  "spo2": 98,
  "battery": 86,
  "ts": 1710000000000
}
```

实际数值会随机变化。

### 模拟测试预期结果

点击后应看到：

- 最近一次数据区域显示血压、心率、血氧、时间。
- 页面提示 `正在上传健康数据`。
- 上传成功后提示 `同步成功`。
- 本次同步记录新增一条记录。
- 回到首页后，血压和心率卡片应更新。

## 真机 BLE 测试步骤

1. 手机开启蓝牙。
2. 使用真机运行小程序。
3. 打开患者端小程序首页。
4. 点击 `设备同步`。
5. 点击 `搜索手表`。
6. 等待出现 `TZB-WATCH-xxx` 设备。
7. 点击设备行进行连接。
8. 页面显示 `手表已连接，等待测量数据`。
9. 在手表端触发测量，或点击小程序 `触发测量`。
10. 手表通过 Notify 上报 JSON。
11. 页面显示最新健康数据。
12. 小程序自动上传数据。

## 上传接口验证

小程序复用现有接口封装：

```text
frontend/patient/api/patient.js -> createMeasurement
```

后端接口：

```text
POST /api/patient/measurements
```

### 血压记录

```json
{
  "type": "bp",
  "value1": 120,
  "value2": 80,
  "measured_at": "2026-05-07T06:36:00.000Z",
  "device_id": "TZB-WATCH-001",
  "notes": "智能手表自动同步，心率 72 bpm"
}
```

### 心率记录

```json
{
  "type": "hr",
  "value1": 72,
  "measured_at": "2026-05-07T06:36:00.000Z",
  "device_id": "TZB-WATCH-001",
  "notes": "智能手表自动同步"
}
```

## 首页显示逻辑

首页现在分别读取：

```text
GET /measurements?type=bp&limit=1
GET /measurements?type=hr&limit=1
```

这样可以避免最新一条心率记录被误显示成血压。

## 常见问题

### 1. 搜索不到设备

检查：

- 手机蓝牙是否开启。
- 是否使用真机调试。
- 固件广播名是否以 `TZB-WATCH` 开头。
- 固件广播中是否包含 Service UUID。
- 手表是否已被其他手机连接。
- 手表是否距离手机过远。

### 2. 能搜到但连接失败

检查：

- 手表是否支持 BLE 外设模式。
- 手表是否允许被当前手机连接。
- 是否已有旧连接未释放。
- 小程序是否反复快速连接导致蓝牙栈异常。

处理方式：

- 关闭页面重新进入。
- 关闭手机蓝牙再打开。
- 重启手表蓝牙广播。

### 3. 连接后提示未找到服务

检查固件是否创建了 Service：

```text
6E400001-B5A3-F393-E0A9-E50E24DCCA9E
```

注意：

- UUID 大小写无关。
- 横杠格式小程序会兼容。
- 但 UUID 内容必须一致。

### 4. 连接后提示未找到通知特征

检查固件是否创建了 Notify Characteristic：

```text
6E400003-B5A3-F393-E0A9-E50E24DCCA9E
```

并且属性必须支持：

```text
notify
```

或：

```text
indicate
```

### 5. 点击触发测量提示不支持指令

说明没有发现可写特征。

检查固件是否创建了 Write Characteristic：

```text
6E400002-B5A3-F393-E0A9-E50E24DCCA9E
```

并且属性支持：

```text
write
```

或：

```text
writeNoResponse
```

### 6. 收到无法解析的数据

说明 Notify 数据不是合法 JSON，或没有按约定发送完整消息。

检查：

- 是否是 UTF-8 编码。
- JSON 是否合法。
- 字符串末尾是否带 `\n`。
- 分包是否按顺序发送。
- 是否混入了调试日志文本。

正确示例：

```text
{"sys":120,"dia":80,"hr":72}\n
```

错误示例：

```text
sys=120,dia=80,hr=72
```

### 7. 页面显示数据但上传失败

检查：

- 患者是否已登录。
- 后端服务是否启动。
- `frontend/patient/config.js` 中 API 地址是否正确。
- 手机是否能访问后端地址。
- 后端 `/api/patient/measurements` 是否正常。

### 8. 首页血压或心率不更新

检查：

- 手表页面是否显示 `同步成功`。
- 后端是否确实保存了 `type=bp` 和 `type=hr` 记录。
- 首页是否重新进入或触发 `onShow`。
- 旧缓存是否还未刷新。

## 微信小程序注意事项

### 真机要求

BLE 最终必须在真机测试。开发者工具不适合作为最终判断。

### 隐私与权限

需要确认小程序后台隐私协议中声明蓝牙用途，例如：

```text
连接智能手表并同步血压、心率等健康数据
```

项目代码中已在 `app.json` 增加蓝牙用途说明。

### Android 注意事项

部分 Android 系统可能要求定位或附近设备权限才能扫描 BLE。若搜索不到设备，需要检查系统权限和微信权限。

### iOS 注意事项

iOS 首次使用蓝牙会弹出权限请求。用户拒绝后，需要到系统设置里重新允许微信使用蓝牙。

## 建议联调记录模板

每次硬件联调建议记录：

```text
日期：
手机型号：
系统版本：
微信版本：
小程序版本：
手表固件版本：
BLE 芯片/模块：
广播名：
是否能搜索：
是否能连接：
是否能订阅 Notify：
是否能收到数据：
是否上传成功：
问题现象：
控制台日志：
处理结论：
```

## 当前已验证内容

已做静态语法检查：

```text
node -c pages/device/device.js
node -c pages/index/index.js
JSON.parse(app.json)
JSON.parse(pages/device/device.json)
```

检查结果：

```text
watch feature syntax ok
```
