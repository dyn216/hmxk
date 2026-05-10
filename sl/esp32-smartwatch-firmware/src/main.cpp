#include <Arduino.h>
#include <Wire.h>
#include <MAX30105.h>
#include <spo2_algorithm.h>
#include <U8g2lib.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

static const char *DEVICE_NAME = "TZB-WATCH-001";
static const char *SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E";
static const char *WRITE_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E";
static const char *NOTIFY_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E";

static const int OLED_SDA_PIN = 8;
static const int OLED_SCL_PIN = 9;
static const int OLED_RESET_PIN = -1;
static const uint8_t OLED_ADDRESS = 0x3C;
static const int MAX30102_SAMPLE_COUNT = 100;
static const int INVALID_VITAL_VALUE = -1;
static const uint32_t MAX30102_FINGER_THRESHOLD = 70000;
static const uint32_t MAX30102_MIN_SIGNAL_SPAN = 1000;
static const int MEASURE_COUNTDOWN_SECONDS = 3;
static const unsigned long MONITOR_INTERVAL_MS = 15000;

struct VitalSigns {
  int systolic;
  int diastolic;
  int heartRate;
  int spo2;
  int battery;
};

BLEServer *bleServer = nullptr;
BLECharacteristic *notifyCharacteristic = nullptr;
BLECharacteristic *writeCharacteristic = nullptr;
U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, OLED_RESET_PIN, OLED_SCL_PIN, OLED_SDA_PIN);
MAX30105 max30102;
uint32_t irBuffer[MAX30102_SAMPLE_COUNT];
uint32_t redBuffer[MAX30102_SAMPLE_COUNT];

bool deviceConnected = false;
bool oldDeviceConnected = false;
bool pendingMeasure = false;
bool displayReady = false;
bool max30102Ready = false;
bool measuringNow = false;
bool monitorActive = false;
bool displayNeedsRefresh = true;
bool hasLastVitalSigns = false;
uint32_t sequenceNo = 1;
unsigned long lastStatusMillis = 0;
unsigned long lastMonitorMeasureMillis = 0;
String displayStatus = "正在启动";
VitalSigns lastVitalSigns = {
  INVALID_VITAL_VALUE,
  INVALID_VITAL_VALUE,
  INVALID_VITAL_VALUE,
  INVALID_VITAL_VALUE,
  INVALID_VITAL_VALUE
};

void requestDisplayRefresh(const String &status) {
  displayStatus = status;
  displayNeedsRefresh = true;
}

String formatVitalValue(int value) {
  return value >= 0 ? String(value) : "----";
}

String formatPercentValue(int value) {
  return value >= 0 ? String(value) + "%" : "----";
}

void resetVitalSigns(VitalSigns &data) {
  data.systolic = INVALID_VITAL_VALUE;
  data.diastolic = INVALID_VITAL_VALUE;
  data.heartRate = INVALID_VITAL_VALUE;
  data.spo2 = INVALID_VITAL_VALUE;
  data.battery = INVALID_VITAL_VALUE;
}

void appendNullableInt(String &payload, const char *field, int value) {
  payload += ",\"";
  payload += field;
  payload += "\":";
  payload += value >= 0 ? String(value) : "null";
}

void refreshDisplay() {
  if (!displayReady || !displayNeedsRefresh) {
    return;
  }

  displayNeedsRefresh = false;
  display.clearBuffer();
  display.setFont(u8g2_font_wqy12_t_gb2312);

  display.drawUTF8(0, 10, "智能手表");
  display.drawUTF8(0, 21, deviceConnected ? "蓝牙：已连接" : "蓝牙：等待连接");
  display.drawUTF8(0, 32, displayStatus.c_str());

  if (hasLastVitalSigns) {
    String bloodPressureLine = "血压：" + formatVitalValue(lastVitalSigns.systolic) + "/" + formatVitalValue(lastVitalSigns.diastolic);
    String heartRateLine = "心率：" + formatVitalValue(lastVitalSigns.heartRate) + " 血氧：" + formatPercentValue(lastVitalSigns.spo2);
    String batteryLine = "电量：" + formatPercentValue(lastVitalSigns.battery);
    display.drawUTF8(0, 43, bloodPressureLine.c_str());
    display.drawUTF8(0, 54, heartRateLine.c_str());
    display.drawUTF8(0, 64, batteryLine.c_str());
  } else if (measuringNow) {
    display.drawUTF8(0, 44, "手指盖住传感器");
    display.drawUTF8(0, 56, "请保持不动");
  } else if (monitorActive) {
    display.drawUTF8(0, 44, "连续监测中");
    display.drawUTF8(0, 56, "自动定时采集");
  } else if (deviceConnected) {
    display.drawUTF8(0, 44, max30102Ready ? "请放好手指" : "检查传感器");
    display.drawUTF8(0, 56, "点击开始测量");
  } else {
    display.drawUTF8(0, 44, "打开患者小程序");
    display.drawUTF8(0, 56, "搜索智能手表");
  }

  display.sendBuffer();
}

void setupDisplay() {
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  display.setI2CAddress(OLED_ADDRESS << 1);
  display.begin();
  display.enableUTF8Print();
  displayReady = true;
  requestDisplayRefresh("屏幕就绪");
  refreshDisplay();
}

void setupMax30102() {
  max30102Ready = max30102.begin(Wire, I2C_SPEED_FAST);
  if (!max30102Ready) {
    Serial.println("MAX30102 init failed");
    requestDisplayRefresh("未找到传感器");
    refreshDisplay();
    return;
  }

  max30102.setup(0x3F, 4, 2, 100, 411, 4096);
  max30102.setPulseAmplitudeRed(0x3F);
  max30102.setPulseAmplitudeIR(0x3F);
  max30102.setPulseAmplitudeGreen(0);
  Serial.println("MAX30102 ready");
  requestDisplayRefresh("传感器就绪");
  refreshDisplay();
}

bool showMeasurementCountdown() {
  if (!max30102Ready) {
    requestDisplayRefresh("未找到传感器");
    refreshDisplay();
    return false;
  }

  measuringNow = true;
  hasLastVitalSigns = false;
  for (int second = MEASURE_COUNTDOWN_SECONDS; second > 0; second--) {
    requestDisplayRefresh("倒计时：" + String(second) + "秒");
    refreshDisplay();
    delay(1000);
  }

  requestDisplayRefresh("正在采集");
  refreshDisplay();
  return true;
}

bool readMax30102(int &heartRate, int &spo2) {
  if (!max30102Ready) {
    requestDisplayRefresh("未找到传感器");
    return false;
  }

  requestDisplayRefresh("正在采集");
  refreshDisplay();
  max30102.clearFIFO();

  uint64_t irTotal = 0;
  uint64_t redTotal = 0;
  uint32_t irMin = 0xFFFFFFFF;
  uint32_t irMax = 0;
  for (int i = 0; i < MAX30102_SAMPLE_COUNT; i++) {
    unsigned long sampleStart = millis();
    while (!max30102.available()) {
      max30102.check();
      if (millis() - sampleStart > 1000) {
        requestDisplayRefresh("传感器超时");
        return false;
      }
      delay(1);
    }

    redBuffer[i] = max30102.getRed();
    irBuffer[i] = max30102.getIR();
    irTotal += irBuffer[i];
    redTotal += redBuffer[i];
    if (irBuffer[i] < irMin) {
      irMin = irBuffer[i];
    }
    if (irBuffer[i] > irMax) {
      irMax = irBuffer[i];
    }
    max30102.nextSample();
  }

  uint32_t irAverage = irTotal / MAX30102_SAMPLE_COUNT;
  uint32_t redAverage = redTotal / MAX30102_SAMPLE_COUNT;
  if (irAverage < MAX30102_FINGER_THRESHOLD || redAverage < MAX30102_FINGER_THRESHOLD || (irMax - irMin) < MAX30102_MIN_SIGNAL_SPAN) {
    requestDisplayRefresh("未检测到手指");
    return false;
  }

  int32_t calculatedSpo2 = 0;
  int8_t validSpo2 = 0;
  int32_t calculatedHeartRate = 0;
  int8_t validHeartRate = 0;

  maxim_heart_rate_and_oxygen_saturation(
    irBuffer,
    MAX30102_SAMPLE_COUNT,
    redBuffer,
    &calculatedSpo2,
    &validSpo2,
    &calculatedHeartRate,
    &validHeartRate
  );

  if (!validHeartRate || calculatedHeartRate < 40 || calculatedHeartRate > 180) {
    requestDisplayRefresh("心率信号不稳");
    return false;
  }

  if (!validSpo2 || calculatedSpo2 < 70 || calculatedSpo2 > 100) {
    requestDisplayRefresh("血氧信号不稳");
    return false;
  }

  heartRate = calculatedHeartRate;
  spo2 = calculatedSpo2;
  return true;
}

bool readVitalSignsFromSensors(VitalSigns &data) {
  resetVitalSigns(data);
  if (!readMax30102(data.heartRate, data.spo2)) {
    return false;
  }
  return true;
}

String buildVitalPayload(const VitalSigns &data) {
  String payload = "{";
  payload += "\"type\":\"vital\"";
  payload += ",\"seq\":" + String(sequenceNo++);
  appendNullableInt(payload, "sys", data.systolic);
  appendNullableInt(payload, "dia", data.diastolic);
  appendNullableInt(payload, "hr", data.heartRate);
  appendNullableInt(payload, "spo2", data.spo2);
  appendNullableInt(payload, "battery", data.battery);
  payload += "}";
  return payload;
}

String buildStatusPayload() {
  String payload = "{";
  payload += "\"type\":\"status\"";
  payload += ",\"seq\":" + String(sequenceNo++);
  payload += "}";
  return payload;
}

void notifyLine(const String &payload) {
  if (!deviceConnected || notifyCharacteristic == nullptr) {
    return;
  }

  String line = payload + "\n";
  const size_t chunkSize = 20;
  size_t offset = 0;

  while (offset < line.length()) {
    String chunk = line.substring(offset, offset + chunkSize);
    notifyCharacteristic->setValue((uint8_t *)chunk.c_str(), chunk.length());
    notifyCharacteristic->notify();
    offset += chunk.length();
    delay(12);
  }

  Serial.print("notify: ");
  Serial.println(payload);
}

void sendVitalSigns(bool monitorMode) {
  VitalSigns data;
  resetVitalSigns(data);
  if (!showMeasurementCountdown()) {
    lastVitalSigns = data;
    hasLastVitalSigns = true;
    measuringNow = false;
    notifyLine(buildVitalPayload(data));
    Serial.println("measurement failed");
    refreshDisplay();
    return;
  }
  if (!readVitalSignsFromSensors(data)) {
    lastVitalSigns = data;
    hasLastVitalSigns = true;
    measuringNow = false;
    notifyLine(buildVitalPayload(data));
    Serial.println("measurement failed");
    refreshDisplay();
    return;
  }
  lastVitalSigns = data;
  hasLastVitalSigns = true;
  measuringNow = false;
  notifyLine(buildVitalPayload(data));
  requestDisplayRefresh(monitorMode ? "监测数据已发送" : "数据已发送");
}

void sendStatus() {
  notifyLine(buildStatusPayload());
}

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *server) override {
    deviceConnected = true;
    Serial.println("central connected");
    requestDisplayRefresh("已连接");
  }

  void onDisconnect(BLEServer *server) override {
    deviceConnected = false;
    monitorActive = false;
    pendingMeasure = false;
    Serial.println("central disconnected");
    requestDisplayRefresh("已断开");
  }
};

class WriteCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *characteristic) override {
    String value = String(characteristic->getValue().c_str());
    value.trim();

    if (value.length() == 0) {
      return;
    }

    Serial.print("write: ");
    Serial.println(value);

    if (value.indexOf("monitor_stop") >= 0 || value.indexOf("stop_monitor") >= 0) {
      monitorActive = false;
      lastMonitorMeasureMillis = 0;
      requestDisplayRefresh("监测已停止");
      return;
    }

    if (value.indexOf("monitor_start") >= 0 || value.indexOf("start_monitor") >= 0 || value.indexOf("\"monitor\"") >= 0) {
      monitorActive = true;
      lastMonitorMeasureMillis = 0;
      requestDisplayRefresh("监测已开启");
      return;
    }

    if (value.indexOf("measure") >= 0) {
      pendingMeasure = true;
      requestDisplayRefresh("准备测量");
      return;
    }

    if (value.indexOf("status") >= 0) {
      sendStatus();
    }
  }
};

void setupBle() {
  BLEDevice::init(DEVICE_NAME);

  bleServer = BLEDevice::createServer();
  bleServer->setCallbacks(new ServerCallbacks());

  BLEService *service = bleServer->createService(SERVICE_UUID);

  notifyCharacteristic = service->createCharacteristic(
    NOTIFY_CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  notifyCharacteristic->addDescriptor(new BLE2902());
  notifyCharacteristic->setValue("ready\n");

  writeCharacteristic = service->createCharacteristic(
    WRITE_CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
  );
  writeCharacteristic->setCallbacks(new WriteCallbacks());

  service->start();

  BLEAdvertising *advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  advertising->setScanResponse(true);
  advertising->setMinPreferred(0x06);
  advertising->setMinPreferred(0x12);

  BLEDevice::startAdvertising();
  Serial.print("advertising as ");
  Serial.println(DEVICE_NAME);
  requestDisplayRefresh("蓝牙就绪");
}

void setup() {
  Serial.begin(115200);
  delay(500);
  setupDisplay();
  setupBle();
  setupMax30102();
}

void loop() {
  if (deviceConnected && pendingMeasure) {
    pendingMeasure = false;
    refreshDisplay();
    sendVitalSigns(false);
    if (monitorActive) {
      lastMonitorMeasureMillis = millis();
    }
  }

  if (deviceConnected && monitorActive && !measuringNow) {
    unsigned long now = millis();
    if (lastMonitorMeasureMillis == 0 || now - lastMonitorMeasureMillis >= MONITOR_INTERVAL_MS) {
      lastMonitorMeasureMillis = now;
      requestDisplayRefresh("连续监测中");
      refreshDisplay();
      sendVitalSigns(true);
      lastMonitorMeasureMillis = millis();
    }
  }

  if (deviceConnected && millis() - lastStatusMillis > 30000) {
    lastStatusMillis = millis();
    sendStatus();
  }

  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    bleServer->startAdvertising();
    Serial.println("restart advertising");
    oldDeviceConnected = deviceConnected;
    requestDisplayRefresh("蓝牙就绪");
  }

  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
    lastStatusMillis = 0;
  }

  refreshDisplay();
  delay(20);
}
