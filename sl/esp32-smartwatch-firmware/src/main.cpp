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
static const unsigned long DISPLAY_ANIMATION_INTERVAL_MS = 360;
static const uint8_t STARTUP_LOGO_WIDTH = 48;
static const uint8_t STARTUP_LOGO_HEIGHT = 48;
static const unsigned char STARTUP_LOGO_BITS[] U8X8_PROGMEM = {
  0x00, 0x00, 0x80, 0x03, 0x00, 0x00, 0x00, 0x00, 0xC0, 0x03, 0x00, 0x00,
  0x00, 0x80, 0xFF, 0xDF, 0x01, 0x00, 0x00, 0x80, 0xF3, 0xC3, 0x03, 0x00,
  0x00, 0xE0, 0xFD, 0xC1, 0x07, 0x00, 0x80, 0x1F, 0x8F, 0x07, 0x1B, 0x00,
  0x80, 0xAF, 0x07, 0x7C, 0xF6, 0x01, 0xC0, 0xCF, 0x01, 0xF0, 0x37, 0x03,
  0x80, 0x6F, 0x00, 0xC0, 0x2F, 0x03, 0x80, 0x3F, 0x00, 0x00, 0xEF, 0x01,
  0xC0, 0x17, 0xF0, 0x0F, 0x9C, 0x02, 0xC0, 0x03, 0xF8, 0x1F, 0x30, 0x07,
  0xF0, 0x03, 0xF8, 0x1F, 0xE0, 0x0C, 0xF8, 0x02, 0xF8, 0x1F, 0xE0, 0x1F,
  0xF8, 0x03, 0xF8, 0x1F, 0xC0, 0x1D, 0x70, 0x01, 0xF8, 0x1F, 0x80, 0x0B,
  0x30, 0xE1, 0xFF, 0xFF, 0x07, 0x15, 0xB8, 0xE1, 0xFF, 0xFF, 0x07, 0x1F,
  0x88, 0xE0, 0xFF, 0xFF, 0x07, 0x1F, 0x88, 0xE0, 0xFF, 0xFF, 0x07, 0x3E,
  0x9C, 0xE0, 0xFF, 0xFF, 0x07, 0x7E, 0x36, 0xE0, 0xFF, 0xFF, 0x07, 0x7E,
  0x32, 0xE0, 0xFF, 0xFF, 0x07, 0x7C, 0x32, 0xE0, 0xFF, 0xFF, 0x07, 0x3C,
  0x7C, 0xE0, 0xFF, 0xFF, 0x07, 0x1C, 0x78, 0x00, 0xF8, 0x1F, 0x00, 0x1E,
  0xD8, 0x00, 0xF8, 0x1F, 0x00, 0x1C, 0xD8, 0x00, 0xFF, 0xFF, 0x00, 0x1D,
  0xB0, 0xC1, 0xFF, 0xFF, 0x03, 0x3C, 0xB0, 0xC1, 0xFB, 0xDF, 0x83, 0x26,
  0xF8, 0xC3, 0xFB, 0xDF, 0x03, 0x24, 0xF8, 0xC3, 0xFF, 0xF7, 0x03, 0x1F,
  0x70, 0xE7, 0x3F, 0xFC, 0x87, 0x05, 0x40, 0xEF, 0xFF, 0xFF, 0xC7, 0x02,
  0xC0, 0x1F, 0xFF, 0xFF, 0xE0, 0x03, 0xC0, 0x1F, 0xFE, 0x7F, 0xF8, 0x01,
  0xC0, 0x3F, 0xF8, 0x1F, 0xFE, 0x03, 0xC0, 0x7F, 0x30, 0x84, 0xF9, 0x03,
  0x80, 0xFF, 0x07, 0xE0, 0xFF, 0x01, 0x00, 0xF8, 0xFF, 0xBF, 0x1F, 0x00,
  0x00, 0xF0, 0xFD, 0xFF, 0x0F, 0x00, 0x00, 0x60, 0xE3, 0xA3, 0x07, 0x00,
  0x00, 0x60, 0xCF, 0xF7, 0x00, 0x00, 0x00, 0xC0, 0x79, 0x1E, 0x00, 0x00,
  0x00, 0x00, 0x60, 0x06, 0x00, 0x00, 0x00, 0x00, 0xC0, 0x03, 0x00, 0x00,
  0x00, 0x00, 0x80, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

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
unsigned long lastDisplayAnimationMillis = 0;
uint8_t displayFrame = 0;
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

bool hasAnyVitalSigns(const VitalSigns &data) {
  return data.systolic >= 0 || data.diastolic >= 0 || data.heartRate >= 0 || data.spo2 >= 0 || data.battery >= 0;
}

bool shouldAnimateDisplay() {
  return measuringNow || monitorActive || !deviceConnected || (deviceConnected && !hasLastVitalSigns);
}

void drawStartupLogo(int x, int y) {
  display.drawXBMP(x, y, STARTUP_LOGO_WIDTH, STARTUP_LOGO_HEIGHT, STARTUP_LOGO_BITS);
}

void drawHeartIcon(int x, int y, bool filled) {
  if (filled) {
    display.drawDisc(x + 4, y + 4, 4);
    display.drawDisc(x + 11, y + 4, 4);
    display.drawBox(x + 2, y + 5, 12, 5);
  } else {
    display.drawCircle(x + 4, y + 4, 4);
    display.drawCircle(x + 11, y + 4, 4);
    display.drawLine(x + 1, y + 6, x + 8, y + 14);
    display.drawLine(x + 15, y + 6, x + 8, y + 14);
  }
  display.drawLine(x + 1, y + 8, x + 8, y + 15);
  display.drawLine(x + 15, y + 8, x + 8, y + 15);
}

void drawBleIcon(int x, int y) {
  display.drawVLine(x + 5, y, 13);
  display.drawLine(x + 5, y, x + 10, y + 4);
  display.drawLine(x + 10, y + 4, x + 5, y + 8);
  display.drawLine(x + 5, y + 8, x + 10, y + 12);
  display.drawLine(x + 10, y + 12, x + 5, y + 13);
  display.drawLine(x + 1, y + 3, x + 9, y + 10);
  display.drawLine(x + 9, y + 3, x + 1, y + 10);
}

void drawSensorIcon(int x, int y) {
  display.drawRFrame(x, y, 23, 18, 4);
  display.drawCircle(x + 11, y + 9, 4);
  display.drawPixel(x + 11, y + 9);
  display.drawLine(x + 4, y + 3, x + 2, y + 1);
  display.drawLine(x + 19, y + 3, x + 21, y + 1);
  display.drawHLine(x + 5, y + 21, 13);
}

void drawPhoneIcon(int x, int y) {
  display.drawRFrame(x, y, 20, 30, 3);
  display.drawHLine(x + 5, y + 4, 10);
  display.drawCircle(x + 10, y + 25, 1);
}

void drawWave(int x, int y, int width, uint8_t frame) {
  int lastX = x;
  int lastY = y;
  for (int i = 0; i <= width; i += 4) {
    int phase = (i / 4 + frame) % 6;
    int yy = y;
    if (phase == 1 || phase == 5) yy = y - 3;
    if (phase == 2 || phase == 4) yy = y + 3;
    display.drawLine(lastX, lastY, x + i, yy);
    lastX = x + i;
    lastY = yy;
  }
}

void drawProgressDots(int x, int y, uint8_t frame) {
  for (int i = 0; i < 4; i++) {
    int radius = ((frame + i) % 4 == 0) ? 3 : 2;
    if ((frame + i) % 4 == 0) {
      display.drawDisc(x + i * 10, y, radius);
    } else {
      display.drawCircle(x + i * 10, y, radius);
    }
  }
}

void drawTopBar() {
  display.drawRFrame(0, 0, 128, 15, 4);
  drawBleIcon(4, 1);
  display.setFont(u8g2_font_wqy12_t_gb2312);
  display.drawUTF8(18, 12, deviceConnected ? "蓝牙已连接" : "等待连接");
  drawHeartIcon(108, 0, (displayFrame % 2) == 0);
}

void drawVitalScene() {
  drawHeartIcon(4, 18, true);
  String bloodPressureLine = formatVitalValue(lastVitalSigns.systolic) + "/" + formatVitalValue(lastVitalSigns.diastolic) + " mmHg";
  display.drawUTF8(24, 29, bloodPressureLine.c_str());
  drawWave(3, 37, 122, displayFrame);
  drawSensorIcon(4, 43);
  String heartRateLine = "心率 " + formatVitalValue(lastVitalSigns.heartRate) + "  血氧 " + formatPercentValue(lastVitalSigns.spo2);
  display.drawUTF8(32, 54, heartRateLine.c_str());
  String batteryLine = "电量 " + formatPercentValue(lastVitalSigns.battery);
  display.drawUTF8(32, 64, batteryLine.c_str());
}

void drawNoDataScene() {
  drawSensorIcon(8, 21);
  display.drawCircle(68, 31, 10 + (displayFrame % 3) * 3);
  display.drawCircle(68, 31, 4);
  display.drawUTF8(82, 30, "未检测到");
  display.drawUTF8(82, 43, "有效数据");
  drawProgressDots(46, 58, displayFrame);
}

void drawMeasuringScene() {
  drawSensorIcon(8, 22);
  display.drawCircle(54, 31, 8 + (displayFrame % 3) * 3);
  display.drawCircle(54, 31, 3);
  display.drawUTF8(72, 28, displayStatus.c_str());
  display.drawUTF8(72, 42, "请保持不动");
  drawProgressDots(45, 58, displayFrame);
}

void drawMonitorScene() {
  drawHeartIcon(8, 20, (displayFrame % 2) == 0);
  drawWave(30, 29, 88, displayFrame);
  drawSensorIcon(8, 42);
  display.drawUTF8(36, 53, "连续监测中");
  drawProgressDots(78, 60, displayFrame);
}

void drawReadyScene() {
  drawBleIcon(10, 23);
  drawSensorIcon(42, 21);
  drawWave(74, 31, 45, displayFrame);
  display.drawUTF8(9, 55, max30102Ready ? "放好手指 点击测量" : "请检查传感器");
}

void drawWaitingScene() {
  drawPhoneIcon(9, 21);
  drawStartupLogo(74, 17);
  display.drawCircle(48, 35, 8 + (displayFrame % 3) * 3);
  display.drawUTF8(33, 58, "小程序搜索手表");
}

void playStartupAnimation() {
  for (int frame = 0; frame < 8; frame++) {
    display.clearBuffer();
    display.setFont(u8g2_font_wqy12_t_gb2312);
    int logoY = 8 - (7 - frame);
    if (logoY < 0) logoY = 0;
    drawStartupLogo(4, logoY);
    display.drawUTF8(58, 20, "惠民携康");
    display.drawUTF8(58, 36, "健康守护");
    display.drawRFrame(58, 47, 64, 7, 3);
    display.drawBox(61, 50, frame * 8, 2);
    display.sendBuffer();
    delay(100);
  }
  for (int frame = 0; frame < 4; frame++) {
    display.clearBuffer();
    drawStartupLogo(4, 4);
    display.drawCircle(28, 28, 24 + frame);
    display.setFont(u8g2_font_wqy12_t_gb2312);
    display.drawUTF8(58, 26, "智能手表");
    display.drawUTF8(58, 43, "启动完成");
    display.sendBuffer();
    delay(120);
  }
}

void refreshDisplay() {
  if (!displayReady) {
    return;
  }

  unsigned long now = millis();
  bool animated = shouldAnimateDisplay();
  if (!displayNeedsRefresh && (!animated || now - lastDisplayAnimationMillis < DISPLAY_ANIMATION_INTERVAL_MS)) {
    return;
  }

  if (animated && now - lastDisplayAnimationMillis >= DISPLAY_ANIMATION_INTERVAL_MS) {
    displayFrame++;
    lastDisplayAnimationMillis = now;
  }

  displayNeedsRefresh = false;
  display.clearBuffer();
  display.setFont(u8g2_font_wqy12_t_gb2312);
  drawTopBar();

  if (hasLastVitalSigns && hasAnyVitalSigns(lastVitalSigns)) {
    drawVitalScene();
  } else if (hasLastVitalSigns) {
    drawNoDataScene();
  } else if (measuringNow) {
    drawMeasuringScene();
  } else if (monitorActive) {
    drawMonitorScene();
  } else if (deviceConnected) {
    drawReadyScene();
  } else {
    drawWaitingScene();
  }

  display.sendBuffer();
}

void setupDisplay() {
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  display.setI2CAddress(OLED_ADDRESS << 1);
  display.begin();
  display.enableUTF8Print();
  display.setBitmapMode(1);
  displayReady = true;
  playStartupAnimation();
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
