# 智能手表固件对接说明

本文档面向智能手表固件开发，说明固件需要实现的 BLE 广播、GATT 服务、数据上报和测量指令处理。

## 固件实现目标

固件需要完成以下能力：

1. 启动 BLE 外设模式。
2. 广播名称使用 `TZB-WATCH` 前缀。
3. 创建智能手表 GATT Service。
4. 创建 Notify Characteristic，用于上报健康数据。
5. 创建 Write Characteristic，用于接收小程序测量指令。
6. 采集或生成血压、心率、血氧、电量等数据。
7. 将数据编码为 UTF-8 JSON，并以 `\n` 结尾发送。

## BLE 广播要求

### 设备名

建议：

```text
TZB-WATCH-001
```

规则：

- 必须以 `TZB-WATCH` 开头。
- 后缀可以用设备编号、MAC 后四位或序列号。

### 广播内容

建议广播中包含主 Service UUID：

```text
6E400001-B5A3-F393-E0A9-E50E24DCCA9E
```

这样即使系统无法读取设备名，小程序也能通过 Service UUID 识别设备。

## GATT 配置

### Service

```text
UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
```

### Notify Characteristic

```text
UUID: 6E400003-B5A3-F393-E0A9-E50E24DCCA9E
Property: notify
Permission: readable is optional, notify required
```

### Write Characteristic

```text
UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
Property: write 或 writeNoResponse
Permission: writable
```

## 上报数据包

### 推荐数据包

```text
{"type":"vital","seq":1,"sys":null,"dia":null,"hr":72,"spo2":98,"battery":null,"ts":1710000000000}\n
```

### 最小可用数据包

如果暂时只有心率和血氧：

```text
{"sys":null,"dia":null,"hr":72,"spo2":98,"battery":null,"ts":1710000000000}\n
```

### 只上报心率

```text
{"hr":72,"battery":null,"ts":1710000000000}\n
```

### 未接入真实血压时

```text
{"sys":null,"dia":null,"battery":null,"ts":1710000000000}\n
```

## 分包建议

BLE 单次通知长度受 MTU 限制，常见默认有效载荷约 20 字节。固件可以采用两种方式：

### 方式一：提高 MTU 后整包发送

如果芯片和手机协商 MTU 成功，可以尽量整包发送。

### 方式二：按字节切片发送

如果保持默认 MTU，可以把完整 JSON 字符串切成多个片段发送。

要求：

- 所有片段按顺序发送。
- 最后一个片段必须包含 `\n`。
- 小程序会把片段拼接到换行符为止，再执行 JSON.parse。

示例完整包：

```text
{"sys":null,"dia":null,"hr":72}\n
```

可以分成：

```text
{"sys":null,
"dia":null,
"hr":72}\n
```

小程序最终会按完整字符串解析。

## 接收测量指令

小程序点击 `触发测量` 后，会写入：

```text
{"cmd":"measure","ts":1710000000000}\n
```

固件收到后建议执行：

1. 解析 JSON。
2. 判断 `cmd` 是否为 `measure`。
3. 启动一次测量流程。
4. 测量完成后通过 Notify Characteristic 上报 `vital` 数据包。

小程序点击 `连续监测` 后，会写入：

```text
{"cmd":"monitor_start","interval_ms":15000,"ts":1710000000000}\n
```

固件收到后建议进入连续监测状态，按固定间隔或 `interval_ms` 建议间隔自动测量并上报。

小程序点击 `停止监测` 后，会写入：

```text
{"cmd":"monitor_stop","ts":1710000000000}\n
```

固件收到后应退出连续监测状态，并停止自动测量。

## 建议状态机

```text
idle
  -> connected
  -> measuring
  -> report_result
  -> connected
  -> monitoring
  -> measuring
  -> report_result
  -> monitoring
```

### idle

- 广播等待连接。
- 可定时进入低功耗模式。

### connected

- 已连接小程序。
- 等待手表本地测量、小程序 `measure` 指令，或 `monitor_start` 指令。

### measuring

- 采集传感器数据。
- 过滤异常值。
- 计算血压、心率等结果。

### report_result

- 封装 JSON。
- 通过 Notify Characteristic 发送。
- 发送完成后回到 `connected` 或 `idle`。

### monitoring

- 按固定间隔自动进入 `measuring`。
- 收到 `monitor_stop` 后回到 `connected`。

## 时间戳建议

如果固件有 RTC 或能从手机同步时间，建议使用真实测量时间。

支持两种格式：

### 毫秒时间戳

```json
{"ts":1710000000000}
```

### 秒时间戳

```json
{"ts":1710000000}
```

小程序会自动判断秒或毫秒。

如果固件暂时没有时间，可以不传 `ts`，小程序会使用收到数据时的手机时间。

## 设备 ID 建议

当前小程序上传时使用：

1. 优先使用 BLE 设备名称。
2. 如果设备名为空，则使用微信返回的 `deviceId`。
3. 如果都没有，则使用 `TZB-WATCH`。

建议固件使用稳定设备名，例如：

```text
TZB-WATCH-001
```

后端记录中会把它作为 `device_id`。

## 数据质量建议

### 血压

如果血压是算法估算结果，建议固件或后续协议增加：

```json
{"bp_source":"estimated"}
```

如果是直接测量结果：

```json
{"bp_source":"measured"}
```

当前小程序不会使用该字段，但后续可扩展。

### 异常数据

不建议上报明显异常数据作为正式结果，例如：

- `sys <= dia`
- `sys < 60`
- `dia < 40`
- `hr < 30`
- `spo2 > 100`

建议固件发送错误包：

```text
{"type":"error","code":"INVALID_READING","message":"invalid vital signs","ts":1710000000000}\n
```

## 联调检查清单

固件烧录后，按以下顺序检查：

- 设备是否能被系统蓝牙扫描到。
- 广播名是否以 `TZB-WATCH` 开头。
- 是否存在 Service `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`。
- Notify Characteristic 是否可订阅。
- Write Characteristic 是否可写。
- 小程序点击 `搜索手表` 是否能发现设备。
- 小程序连接后是否显示 `手表已连接，等待测量数据`。
- 手表上报 JSON 后页面是否显示血压、心率、血氧。
- 后端是否新增 `bp` 和 `hr` 两条测量记录。
