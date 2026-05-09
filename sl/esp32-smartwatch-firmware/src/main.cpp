#include <Arduino.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

static const char *DEVICE_NAME = "TZB-WATCH-001";
static const char *SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E";
static const char *WRITE_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E";
static const char *NOTIFY_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E";

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

bool deviceConnected = false;
bool oldDeviceConnected = false;
bool pendingMeasure = false;
uint32_t sequenceNo = 1;
uint8_t batteryLevel = 86;
unsigned long lastStatusMillis = 0;

VitalSigns readVitalSignsFromSensors() {
  VitalSigns data;
  data.systolic = 112 + random(0, 24);
  data.diastolic = 70 + random(0, 15);
  if (data.diastolic >= data.systolic) {
    data.diastolic = data.systolic - 35;
  }
  data.heartRate = 66 + random(0, 22);
  data.spo2 = 96 + random(0, 4);
  data.battery = batteryLevel;
  return data;
}

String buildVitalPayload(const VitalSigns &data) {
  String payload = "{";
  payload += "\"type\":\"vital\"";
  payload += ",\"seq\":" + String(sequenceNo++);
  payload += ",\"sys\":" + String(data.systolic);
  payload += ",\"dia\":" + String(data.diastolic);
  payload += ",\"hr\":" + String(data.heartRate);
  payload += ",\"spo2\":" + String(data.spo2);
  payload += ",\"battery\":" + String(data.battery);
  payload += "}";
  return payload;
}

String buildStatusPayload() {
  String payload = "{";
  payload += "\"type\":\"status\"";
  payload += ",\"seq\":" + String(sequenceNo++);
  payload += ",\"battery\":" + String(batteryLevel);
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

void sendVitalSigns() {
  VitalSigns data = readVitalSignsFromSensors();
  notifyLine(buildVitalPayload(data));
}

void sendStatus() {
  notifyLine(buildStatusPayload());
}

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *server) override {
    deviceConnected = true;
    Serial.println("central connected");
  }

  void onDisconnect(BLEServer *server) override {
    deviceConnected = false;
    Serial.println("central disconnected");
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

    if (value.indexOf("measure") >= 0) {
      pendingMeasure = true;
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
}

void setup() {
  Serial.begin(115200);
  delay(500);
  randomSeed((uint32_t)esp_random());
  setupBle();
}

void loop() {
  if (deviceConnected && pendingMeasure) {
    pendingMeasure = false;
    sendVitalSigns();
  }

  if (deviceConnected && millis() - lastStatusMillis > 30000) {
    lastStatusMillis = millis();
    sendStatus();
    if (batteryLevel > 5) {
      batteryLevel--;
    }
  }

  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    bleServer->startAdvertising();
    Serial.println("restart advertising");
    oldDeviceConnected = deviceConnected;
  }

  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
    lastStatusMillis = 0;
  }

  delay(20);
}
