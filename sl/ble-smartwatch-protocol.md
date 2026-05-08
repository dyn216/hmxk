# 智能手表 BLE 协议定义

本文档定义自研智能手表与患者端微信小程序之间的 BLE 通信协议。当前协议按 BLE UART 风格设计，适合 ESP32、nRF52 等可自定义 GATT 服务的蓝牙芯片。

## 设备广播

### 广播名称

设备名必须以以下前缀开头：

```text
TZB-WATCH
```

推荐命名：

```text
TZB-WATCH-001
TZB-WATCH-002
```

小程序扫描时会匹配：

- 设备名以 `TZB-WATCH` 开头
- 或广播中包含目标 Service UUID

## GATT 服务

### Service UUID

```text
6E400001-B5A3-F393-E0A9-E50E24DCCA9E
```

这是智能手表主服务，小程序连接设备后会查找该服务。

## GATT 特征

### Notify Characteristic

手表向小程序上报健康数据使用该特征：

```text
6E400003-B5A3-F393-E0A9-E50E24DCCA9E
```

要求：

- 属性支持 `notify`，也可以兼容 `indicate`。
- 数据编码为 UTF-8。
- 每条完整消息以换行符 `\n` 结束。
- 单条 JSON 可以被 BLE 分包，小程序会自动拼接到换行符为止。

### Write Characteristic

小程序向手表发送控制指令使用该特征：

```text
6E400002-B5A3-F393-E0A9-E50E24DCCA9E
```

要求：

- 属性支持 `write` 或 `writeNoResponse`。
- 数据编码为 UTF-8。
- 每条指令以换行符 `\n` 结束。

## 手表上报数据格式

手表通过 Notify Characteristic 上报 JSON。

### 示例

```json
{"type":"vital","seq":1,"sys":120,"dia":80,"hr":72,"spo2":98,"battery":86,"ts":1710000000000}
```

实际发送内容末尾需要包含换行符：

```text
{"type":"vital","seq":1,"sys":120,"dia":80,"hr":72,"spo2":98,"battery":86,"ts":1710000000000}\n
```

## 字段定义

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | 否 | 建议固定为 `vital` |
| `seq` | number/string | 否 | 数据序号，用于排查重复数据 |
| `sys` | number | 血压数据必填 | 收缩压，单位 mmHg |
| `dia` | number | 血压数据必填 | 舒张压，单位 mmHg |
| `hr` | number | 心率数据必填 | 心率，单位 bpm |
| `spo2` | number | 否 | 血氧，单位 `%` |
| `temperature` | number | 否 | 体温，单位摄氏度 |
| `battery` | number | 否 | 电量百分比，0-100 |
| `ts` | number | 否 | 测量时间戳，支持秒或毫秒 |

## 兼容字段

小程序当前兼容以下字段名：

| 标准字段 | 兼容字段 |
| --- | --- |
| `sys` | `systolic` |
| `dia` | `diastolic` |
| `hr` | `heart_rate` |

## 小程序发送指令格式

点击 `触发测量` 时，小程序会通过 Write Characteristic 发送：

```json
{"cmd":"measure","ts":1710000000000}
```

实际发送内容末尾包含换行符：

```text
{"cmd":"measure","ts":1710000000000}\n
```

### 指令字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `cmd` | string | 指令名，当前为 `measure` |
| `ts` | number | 小程序发送指令时的本机毫秒时间戳 |

## 上传到后端的数据映射

小程序收到手表数据后，会调用现有患者端测量数据接口。

### 血压上传

当同时存在 `sys` 和 `dia` 时，上传血压记录：

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

### 心率上传

当存在 `hr` 时，上传心率记录：

```json
{
  "type": "hr",
  "value1": 72,
  "measured_at": "2026-05-07T06:36:00.000Z",
  "device_id": "TZB-WATCH-001",
  "notes": "智能手表自动同步"
}
```

## 数据边界建议

固件侧建议先做基础校验：

| 指标 | 建议范围 |
| --- | --- |
| 收缩压 `sys` | 60-250 mmHg |
| 舒张压 `dia` | 40-160 mmHg |
| 心率 `hr` | 30-220 bpm |
| 血氧 `spo2` | 70-100% |
| 电量 `battery` | 0-100% |

超出范围的数据不建议直接上报为正式测量结果，可以上报错误状态或要求重新测量。

## 错误或状态数据建议

后续可以扩展状态包，例如：

```json
{"type":"status","battery":86,"charging":false,"ts":1710000000000}
```

或错误包：

```json
{"type":"error","code":"SENSOR_TIMEOUT","message":"measurement timeout","ts":1710000000000}
```

当前小程序主要处理健康数据包，状态包只会更新页面状态，不会上传为血压或心率记录。
