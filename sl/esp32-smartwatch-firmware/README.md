# ESP32 智能手表 BLE 固件示例

这是按患者端小程序 BLE 协议编写的 ESP32-C3 SuperMini 固件示例。烧录后，开发板会广播为 `TZB-WATCH-001`，小程序可搜索、连接、发送测量指令，并接收血压、心率、血氧数据。当前版本已加入 0.96 寸 I2C OLED 显示和 MAX30102 心率血氧传感器读取。

## 适用硬件

- ESP32-C3 SuperMini
- 0.96 寸 I2C OLED，常见 SSD1306，128x64，地址 `0x3C`
- MAX30102 心率血氧传感器模块，I2C 地址常见为 `0x57`

如果你的手表蓝牙主控不是 ESP32，也可以参考 `src/main.cpp` 中的协议、UUID 和 JSON 发送方式移植。

## OLED 接线

默认代码使用：

```text
SDA = GPIO8
SCL = GPIO9
OLED 地址 = 0x3C
分辨率 = 128x64
```

接线：

| OLED | ESP32-C3 SuperMini |
| --- | --- |
| `GND` | `GND` |
| `VCC` | `3V3` |
| `SDA` | `GPIO8` |
| `SCL` | `GPIO9` |

如果你的开发板在接 `GPIO9` 后无法烧录或无法启动，先拔掉 OLED 的 `SCL` 再烧录；也可以把代码里的 `OLED_SDA_PIN` 和 `OLED_SCL_PIN` 改成其他可用 GPIO。

## MAX30102 接线

MAX30102 和 OLED 都是 I2C 设备，可以共用同一组 `SDA/SCL`。默认代码继续使用：

```text
SDA = GPIO8
SCL = GPIO9
MAX30102 地址 = 0x57
```

接线：

| MAX30102 | ESP32-C3 SuperMini |
| --- | --- |
| `GND` | `GND` |
| `VIN`/`VCC` | `3V3` |
| `SDA` | `GPIO8` |
| `SCL` | `GPIO9` |
| `INT` | 不接 |

注意：MAX30102 模块建议用 `3V3` 供电。不要把模块接到 `5V` 后再把 `SDA/SCL` 直接接 ESP32-C3，因为部分模块会把 I2C 上拉到供电电压，可能损坏 ESP32-C3。

如果 OLED 和 MAX30102 同时接上后显示或传感器不稳定，先只接 MAX30102 测试；确认正常后再把 OLED 并到同一组 `SDA/SCL`。

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

小程序点击 `连续监测` 时，会写入：

```text
{"cmd":"monitor_start","interval_ms":15000,"ts":1710000000000}\n
```

小程序点击 `停止监测` 时，会写入：

```text
{"cmd":"monitor_stop","ts":1710000000000}\n
```

当前示例固件连续监测间隔固定为 15 秒。

### Notify Characteristic

```text
6E400003-B5A3-F393-E0A9-E50E24DCCA9E
```

固件通过 Notify 分包发送：

```text
{"type":"vital","seq":1,"sys":null,"dia":null,"hr":72,"spo2":98,"battery":null}\n
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
3. 在 Arduino IDE 的库管理器安装：

```text
SparkFun MAX3010x Pulse and Proximity Sensor Library
U8g2
```

4. 打开文件：

```text
arduino/TZBWatchBle/TZBWatchBle.ino
```

5. 开发板选择：

```text
ESP32C3 Dev Module
```

6. 选择正确串口。
7. 点击上传。
8. 打开串口监视器，波特率选择：

```text
115200
```

## 小程序联调步骤

1. 烧录固件。
2. ESP32-C3 上电。
3. 串口看到：

```text
advertising as TZB-WATCH-001
```

4. OLED 应显示 `智能手表`，蓝牙行显示 `蓝牙：等待连接`，状态行显示 `传感器就绪` 或 `蓝牙就绪`。
5. 打开患者端小程序。
6. 进入 `设备同步`。
7. 点击 `搜索手表`。
8. 点击 `TZB-WATCH-001` 连接。
9. OLED 应显示 `蓝牙：已连接`。
10. 手指轻轻覆盖 MAX30102 的红光/红外光窗口。
11. 点击 `触发测量`。
12. OLED 会显示 `倒计时：3秒`、`倒计时：2秒`、`倒计时：1秒`，随后显示 `正在采集`。读取成功后 OLED 和小程序页面应显示血压、心率、血氧、电量。
13. 点击 `连续监测` 后，OLED 会显示 `监测已开启` 或 `连续监测中`，固件会约每 15 秒自动采集并上报一次。
14. 点击 `停止监测` 后，OLED 会显示 `监测已停止`，固件停止自动采集。
15. 单次测量上传成功后会出现 `同步成功`；连续监测数据会自动上传，不会每次弹出成功提示。

## 当前代码的数据来源

当前代码的数据来源如下：

| 字段 | 数据来源 |
| --- | --- |
| `hr` | MAX30102 实测心率 |
| `spo2` | MAX30102 实测血氧 |
| `sys` | 未接入真实血压传感器，固定为空 |
| `dia` | 未接入真实血压传感器，固定为空 |
| `battery` | 未接入真实电量检测，固定为空 |

MAX30102 不能直接测血压，所以当前版本只上报真实心率和真实血氧；血压和电量不再使用模拟值，没有真实数据时 JSON 中为 `null`，OLED 和小程序显示 `----`。后续如果要做真实血压，需要额外的血压传感器或经过校准的算法。

读取入口在：

```text
src/main.cpp -> readVitalSignsFromSensors()
```

或 Arduino IDE 版本：

```text
arduino/TZBWatchBle/TZBWatchBle.ino -> readVitalSignsFromSensors()
```

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

如果测试连续监测，串口应能看到：

```text
write: {"cmd":"monitor_start",...}
```

如果没有，说明小程序没有写入成功，检查 Write Characteristic UUID。

如果 OLED 显示 `未找到传感器`，检查：

- MAX30102 的 `VCC/VIN` 是否接 `3V3`。
- MAX30102 的 `GND` 是否和 ESP32-C3 共地。
- `SDA` 是否接 `GPIO8`。
- `SCL` 是否接 `GPIO9`。
- 面包板跳线是否松动。

如果 OLED 显示 `未检测到手指`、`心率信号不稳` 或 `血氧信号不稳`，说明传感器已识别但信号不稳定。测试时手指要完全覆盖传感器窗口，保持 2-5 秒不要移动，环境强光下可以用手遮挡一下模块。

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
