# ESP32 智能手表 BLE 固件示例

这是按患者端小程序 BLE 协议编写的 ESP32 固件示例。烧录后，ESP32 会广播为 `TZB-WATCH-001`，小程序可搜索、连接、发送测量指令，并接收模拟血压/心率数据。

## 适用硬件

- ESP32 DevKit
- ESP32-WROOM-32
- 其他兼容 Arduino ESP32 Core 的 ESP32 开发板

如果你的手表蓝牙主控不是 ESP32，也可以参考 `src/main.cpp` 中的协议、UUID 和 JSON 发送方式移植。

## 文件结构

```text
esp32-smartwatch-firmware/
├── README.md
├── platformio.ini
├── src/
│   └── main.cpp
└── arduino/
    └── TZBWatchBle/
        └── TZBWatchBle.ino
```

## BLE 协议

### 设备名

```text
TZB-WATCH-001
```

### Service UUID

```text
6E400001-B5A3-F393-E0A9-E50E24DCCA9E
```

### Write Characteristic

```text
6E400002-B5A3-F393-E0A9-E50E24DCCA9E
```

小程序点击 `触发测量` 时，会写入：

```text
{"cmd":"measure","ts":1710000000000}\n
```

### Notify Characteristic

```text
6E400003-B5A3-F393-E0A9-E50E24DCCA9E
```

固件通过 Notify 分包发送：

```text
{"type":"vital","seq":1,"sys":120,"dia":80,"hr":72,"spo2":98,"battery":86}\n
```

## 使用 PlatformIO 烧录

在当前目录执行：

```bash
pio run -t upload
```

打开串口监视器：

```bash
pio device monitor
```

如果串口不是自动识别，可在 `platformio.ini` 增加：

```ini
upload_port = /dev/ttyUSB0
monitor_port = /dev/ttyUSB0
```

常见端口：

```text
Linux: /dev/ttyUSB0 或 /dev/ttyACM0
Windows: COM3、COM4 等
macOS: /dev/cu.usbserial-xxxx
```

## 使用 Arduino IDE 烧录

1. 安装 Arduino IDE。
2. 安装 ESP32 开发板支持。
3. 打开文件：

```text
arduino/TZBWatchBle/TZBWatchBle.ino
```

4. 开发板选择：

```text
ESP32 Dev Module
```

5. 选择正确串口。
6. 点击上传。
7. 打开串口监视器，波特率选择：

```text
115200
```

## 小程序联调步骤

1. 烧录固件。
2. ESP32 上电。
3. 串口看到：

```text
advertising as TZB-WATCH-001
```

4. 打开患者端小程序。
5. 进入 `设备同步`。
6. 点击 `搜索手表`。
7. 点击 `TZB-WATCH-001` 连接。
8. 点击 `触发测量`。
9. 页面应显示血压、心率、血氧、电量。
10. 上传成功后会出现 `同步成功`。

## 当前代码的数据来源

当前示例代码使用模拟数据：

```cpp
VitalSigns readVitalSignsFromSensors() {
  VitalSigns data;
  data.systolic = 112 + random(0, 24);
  data.diastolic = 70 + random(0, 15);
  data.heartRate = 66 + random(0, 22);
  data.spo2 = 96 + random(0, 4);
  data.battery = batteryLevel;
  return data;
}
```

后续接入真实传感器时，只需要替换这个函数，让它返回真实数据。

## 接真实传感器时需要改哪里

主要改：

```text
src/main.cpp -> readVitalSignsFromSensors()
```

或 Arduino IDE 版本：

```text
arduino/TZBWatchBle/TZBWatchBle.ino -> readVitalSignsFromSensors()
```

把：

```cpp
data.systolic = 112 + random(0, 24);
data.diastolic = 70 + random(0, 15);
data.heartRate = 66 + random(0, 22);
data.spo2 = 96 + random(0, 4);
```

替换为真实传感器读取结果。

## 为什么 JSON 里没有 ts

ESP32 示例默认没有联网和 RTC，无法保证真实时间。因此示例固件不发送 `ts` 字段。

小程序收到没有 `ts` 的数据时，会自动使用手机接收时间作为测量时间。

如果后续固件有 RTC 或 NTP，可以增加：

```text
,"ts":1710000000000
```

## 分包策略

代码中按 20 字节分包 Notify：

```cpp
const size_t chunkSize = 20;
```

这样兼容默认 BLE MTU。小程序会按换行符 `\n` 自动拼包。

## 常见问题

### 小程序搜不到设备

检查：

- ESP32 是否已上电。
- 串口是否输出 `advertising as TZB-WATCH-001`。
- 手机蓝牙是否开启。
- 是否使用真机调试。
- ESP32 是否已经被其他手机连接。

### 能连接但点触发测量没有数据

检查串口是否收到：

```text
write: {"cmd":"measure",...}
```

如果没有，说明小程序没有写入成功，检查 Write Characteristic UUID。

### 页面提示收到无法解析的数据

检查 Notify 数据是否为合法 JSON，并且末尾是否有 `\n`。

### 上传失败

BLE 已通，但后端或登录状态有问题。检查：

- 小程序患者是否已登录。
- 后端服务是否启动。
- 手机是否能访问后端接口。

## 后续建议

- 接入真实心率/血氧传感器后，先只替换 `hr` 和 `spo2`。
- 血压如果是算法估算，建议后续增加 `bp_source` 字段标记来源。
- 如果需要低功耗，再增加连接空闲超时和深睡眠逻辑。
