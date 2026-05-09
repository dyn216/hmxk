var patientApi = require('../../api/patient.js');

var WATCH_PROTOCOL = {
  namePrefix: 'TZB-WATCH',
  serviceId: '6E400001-B5A3-F393-E0A9-E50E24DCCA9E',
  notifyCharacteristicId: '6E400003-B5A3-F393-E0A9-E50E24DCCA9E',
  writeCharacteristicId: '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
};

function normalizeUuid(value) {
  return String(value || '').replace(/-/g, '').toLowerCase();
}

function numberOrNull(value) {
  var num = Number(value);
  return isNaN(num) ? null : num;
}

function formatTime(date) {
  var hour = date.getHours();
  var minute = date.getMinutes();
  var second = date.getSeconds();
  return [
    hour < 10 ? '0' + hour : hour,
    minute < 10 ? '0' + minute : minute,
    second < 10 ? '0' + second : second
  ].join(':');
}

Page({
  data: {
    protocol: WATCH_PROTOCOL,
    bluetoothReady: false,
    discovering: false,
    connecting: false,
    connected: false,
    deviceId: '',
    deviceName: '',
    statusText: '等待连接智能手表',
    lastSyncText: '尚未同步',
    battery: '--',
    rssi: '--',
    devices: [],
    lastPacket: null,
    recentRecords: [],
    uploading: false,
    receiveBuffer: '',
    serviceId: '',
    notifyCharacteristicId: '',
    writeCharacteristicId: '',
    lastSignature: ''
  },

  onLoad: function() {
    this.valueChangeHandler = this.handleBleValueChange.bind(this);
    this.deviceFoundHandler = this.handleDeviceFound.bind(this);
  },

  onUnload: function() {
    this.closeConnection();
    if (wx.offBluetoothDeviceFound && this.deviceFoundHandler) {
      wx.offBluetoothDeviceFound(this.deviceFoundHandler);
    }
    if (wx.offBLECharacteristicValueChange && this.valueChangeHandler) {
      wx.offBLECharacteristicValueChange(this.valueChangeHandler);
    }
    wx.stopBluetoothDevicesDiscovery({});
    wx.closeBluetoothAdapter({});
  },

  startScan: function() {
    var self = this;
    if (this.data.discovering || this.data.connecting) return;
    this.setData({
      devices: [],
      statusText: '正在初始化蓝牙',
      discovering: true
    });
    wx.openBluetoothAdapter({
      success: function() {
        self.setData({
          bluetoothReady: true,
          statusText: '正在搜索 ' + WATCH_PROTOCOL.namePrefix
        });
        if (wx.offBluetoothDeviceFound && self.deviceFoundHandler) {
          wx.offBluetoothDeviceFound(self.deviceFoundHandler);
        }
        wx.onBluetoothDeviceFound(self.deviceFoundHandler);
        wx.startBluetoothDevicesDiscovery({
          allowDuplicatesKey: false,
          services: [],
          success: function() {
            self.setData({ discovering: true });
          },
          fail: function(err) {
            self.setData({
              discovering: false,
              statusText: err.errMsg || '蓝牙搜索失败'
            });
            wx.showToast({
              title: '蓝牙搜索失败',
              icon: 'none'
            });
          }
        });
      },
      fail: function(err) {
        self.setData({
          bluetoothReady: false,
          discovering: false,
          statusText: '请开启手机蓝牙后重试'
        });
        wx.showModal({
          title: '蓝牙不可用',
          content: err.errMsg || '请开启手机蓝牙，并允许微信使用蓝牙。',
          showCancel: false
        });
      }
    });
  },

  stopScan: function() {
    wx.stopBluetoothDevicesDiscovery({});
    this.setData({
      discovering: false,
      statusText: this.data.connected ? '手表已连接' : '已停止搜索'
    });
  },

  handleDeviceFound: function(res) {
    var found = res.devices || [];
    var devices = this.data.devices.slice();
    var serviceUuid = normalizeUuid(WATCH_PROTOCOL.serviceId);
    var i;
    for (i = 0; i < found.length; i++) {
      var device = found[i] || {};
      var name = device.name || device.localName || '';
      var services = device.advertisServiceUUIDs || [];
      var matchedName = name.indexOf(WATCH_PROTOCOL.namePrefix) === 0;
      var matchedService = services.some(function(uuid) {
        return normalizeUuid(uuid) === serviceUuid;
      });
      if (!matchedName && !matchedService) continue;
      var item = {
        deviceId: device.deviceId,
        name: name || WATCH_PROTOCOL.namePrefix,
        rssi: device.RSSI || '--'
      };
      var exists = false;
      var j;
      for (j = 0; j < devices.length; j++) {
        if (devices[j].deviceId === item.deviceId) {
          devices[j] = item;
          exists = true;
          break;
        }
      }
      if (!exists) devices.push(item);
    }
    devices.sort(function(a, b) {
      return Number(b.rssi || -100) - Number(a.rssi || -100);
    });
    this.setData({ devices: devices });
  },

  connectDevice: function(e) {
    var deviceId = e.currentTarget.dataset.id;
    var name = e.currentTarget.dataset.name || WATCH_PROTOCOL.namePrefix;
    var rssi = e.currentTarget.dataset.rssi || '--';
    if (!deviceId || this.data.connecting) return;
    this.stopScan();
    this.setData({
      connecting: true,
      statusText: '正在连接 ' + name,
      deviceId: deviceId,
      deviceName: name,
      rssi: rssi
    });
    var self = this;
    wx.createBLEConnection({
      deviceId: deviceId,
      timeout: 10000,
      success: function() {
        self.setData({
          connected: true,
          connecting: false,
          statusText: '正在发现手表服务'
        });
        self.discoverServices();
      },
      fail: function(err) {
        self.setData({
          connected: false,
          connecting: false,
          statusText: err.errMsg || '连接失败'
        });
        wx.showToast({
          title: '连接失败',
          icon: 'none'
        });
      }
    });
  },

  discoverServices: function() {
    var self = this;
    wx.getBLEDeviceServices({
      deviceId: this.data.deviceId,
      success: function(res) {
        var services = res.services || [];
        var target = null;
        var serviceUuid = normalizeUuid(WATCH_PROTOCOL.serviceId);
        var i;
        for (i = 0; i < services.length; i++) {
          if (normalizeUuid(services[i].uuid) === serviceUuid) {
            target = services[i];
            break;
          }
        }
        if (!target) {
          self.setData({
            statusText: '未找到智能手表服务，请检查固件协议'
          });
          return;
        }
        self.setData({
          serviceId: target.uuid,
          statusText: '正在订阅手表数据'
        });
        self.discoverCharacteristics(target.uuid);
      },
      fail: function(err) {
        self.setData({
          statusText: err.errMsg || '读取蓝牙服务失败'
        });
      }
    });
  },

  discoverCharacteristics: function(serviceId) {
    var self = this;
    wx.getBLEDeviceCharacteristics({
      deviceId: this.data.deviceId,
      serviceId: serviceId,
      success: function(res) {
        var list = res.characteristics || [];
        var notifyUuid = normalizeUuid(WATCH_PROTOCOL.notifyCharacteristicId);
        var writeUuid = normalizeUuid(WATCH_PROTOCOL.writeCharacteristicId);
        var notifyChar = null;
        var writeChar = null;
        var i;
        for (i = 0; i < list.length; i++) {
          var item = list[i];
          var uuid = normalizeUuid(item.uuid);
          var props = item.properties || {};
          if (uuid === notifyUuid || props.notify || props.indicate) {
            if (!notifyChar || uuid === notifyUuid) notifyChar = item;
          }
          if (uuid === writeUuid || props.write || props.writeNoResponse) {
            if (!writeChar || uuid === writeUuid) writeChar = item;
          }
        }
        if (!notifyChar) {
          self.setData({
            statusText: '未找到通知特征，请检查固件协议'
          });
          return;
        }
        self.setData({
          notifyCharacteristicId: notifyChar.uuid,
          writeCharacteristicId: writeChar ? writeChar.uuid : '',
          statusText: '正在开启数据通知'
        });
        self.enableNotify();
      },
      fail: function(err) {
        self.setData({
          statusText: err.errMsg || '读取特征失败'
        });
      }
    });
  },

  enableNotify: function() {
    var self = this;
    if (wx.offBLECharacteristicValueChange && this.valueChangeHandler) {
      wx.offBLECharacteristicValueChange(this.valueChangeHandler);
    }
    wx.onBLECharacteristicValueChange(this.valueChangeHandler);
    wx.notifyBLECharacteristicValueChange({
      state: true,
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      characteristicId: this.data.notifyCharacteristicId,
      success: function() {
        self.setData({
          statusText: '手表已连接，等待测量数据',
          lastSyncText: '等待手表上报'
        });
      },
      fail: function(err) {
        self.setData({
          statusText: err.errMsg || '订阅通知失败'
        });
      }
    });
  },

  handleBleValueChange: function(res) {
    if (res.deviceId !== this.data.deviceId) return;
    var text = this.arrayBufferToString(res.value);
    this.consumePacketText(text);
  },

  consumePacketText: function(text) {
    var buffer = this.data.receiveBuffer + text;
    var parts = buffer.split(/\r?\n/);
    var complete = parts.slice(0, parts.length - 1);
    var tail = parts[parts.length - 1];
    if (complete.length === 0) {
      var candidate = buffer.trim();
      if (candidate.charAt(0) === '{' && candidate.charAt(candidate.length - 1) === '}') {
        this.setData({ receiveBuffer: '' });
        this.handlePacketText(candidate);
      } else {
        this.setData({ receiveBuffer: buffer });
      }
      return;
    }
    var i;
    for (i = 0; i < complete.length; i++) {
      this.handlePacketText(complete[i]);
    }
    this.setData({ receiveBuffer: tail });
  },

  handlePacketText: function(text) {
    var payload = String(text || '').trim();
    if (!payload) return;
    var packet;
    try {
      packet = JSON.parse(payload);
    } catch (err) {
      this.setData({
        statusText: '收到无法解析的数据'
      });
      return;
    }
    this.handleWatchPacket(packet);
  },

  handleWatchPacket: function(packet) {
    var systolic = numberOrNull(packet.systolic !== undefined ? packet.systolic : packet.sys);
    var diastolic = numberOrNull(packet.diastolic !== undefined ? packet.diastolic : packet.dia);
    var heartRate = numberOrNull(packet.heart_rate !== undefined ? packet.heart_rate : packet.hr);
    var battery = numberOrNull(packet.battery);
    var measuredAt = this.resolveMeasuredAt(packet.ts);
    var normalized = {
      seq: packet.seq || '',
      systolic: systolic,
      diastolic: diastolic,
      heartRate: heartRate,
      spo2: numberOrNull(packet.spo2),
      temperature: numberOrNull(packet.temperature),
      battery: battery,
      measuredAt: measuredAt.toISOString(),
      receivedAtText: formatTime(new Date())
    };
    var signature = JSON.stringify(normalized);
    if (signature === this.data.lastSignature) return;
    this.setData({
      lastSignature: signature,
      lastPacket: normalized,
      battery: battery === null ? this.data.battery : battery,
      lastSyncText: '收到数据 ' + normalized.receivedAtText,
      statusText: '已收到手表数据'
    });
    this.uploadWatchMeasurements(normalized);
  },

  resolveMeasuredAt: function(ts) {
    if (!ts) return new Date();
    var num = Number(ts);
    if (isNaN(num)) return new Date();
    if (num < 10000000000) num = num * 1000;
    return new Date(num);
  },

  uploadWatchMeasurements: function(data) {
    var tasks = [];
    var deviceId = this.data.deviceName || this.data.deviceId || WATCH_PROTOCOL.namePrefix;
    if (data.systolic && data.diastolic) {
      tasks.push(patientApi.createMeasurement({
        type: 'bp',
        value1: data.systolic,
        value2: data.diastolic,
        measured_at: data.measuredAt,
        device_id: deviceId,
        notes: '智能手表自动同步' + (data.heartRate ? '，心率 ' + data.heartRate + ' bpm' : '')
      }));
    }
    if (data.heartRate) {
      tasks.push(patientApi.createMeasurement({
        type: 'hr',
        value1: data.heartRate,
        measured_at: data.measuredAt,
        device_id: deviceId,
        notes: '智能手表自动同步'
      }));
    }
    if (tasks.length === 0) {
      this.setData({
        statusText: '收到设备状态数据'
      });
      return;
    }
    var self = this;
    this.setData({
      uploading: true,
      statusText: '正在上传健康数据'
    });
    Promise.all(tasks).then(function() {
      var records = self.data.recentRecords.slice();
      records.unshift(data);
      self.setData({
        uploading: false,
        recentRecords: records.slice(0, 5),
        lastSyncText: '已上传 ' + data.receivedAtText,
        statusText: '健康数据已上传'
      });
      wx.showToast({
        title: '同步成功',
        icon: 'success'
      });
    }).catch(function(err) {
      self.setData({
        uploading: false,
        statusText: err.message || '上传失败'
      });
      wx.showToast({
        title: '上传失败',
        icon: 'none'
      });
    });
  },

  sendMeasureCommand: function() {
    if (!this.data.connected || !this.data.writeCharacteristicId) {
      wx.showToast({
        title: '手表未连接或不支持指令',
        icon: 'none'
      });
      return;
    }
    var command = {
      cmd: 'measure',
      ts: Date.now()
    };
    wx.writeBLECharacteristicValue({
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      characteristicId: this.data.writeCharacteristicId,
      value: this.stringToArrayBuffer(JSON.stringify(command) + '\n'),
      success: function() {
        wx.showToast({
          title: '已发送测量指令',
          icon: 'none'
        });
      },
      fail: function() {
        wx.showToast({
          title: '指令发送失败',
          icon: 'none'
        });
      }
    });
  },

  simulatePacket: function() {
    var systolic = 116 + Math.floor(Math.random() * 18);
    var diastolic = 72 + Math.floor(Math.random() * 12);
    var heartRate = 68 + Math.floor(Math.random() * 18);
    this.handleWatchPacket({
      type: 'vital',
      seq: Date.now(),
      sys: systolic,
      dia: diastolic,
      hr: heartRate,
      spo2: 96 + Math.floor(Math.random() * 3),
      battery: this.data.battery === '--' ? 86 : this.data.battery,
      ts: Date.now()
    });
  },

  closeConnection: function() {
    if (this.data.deviceId) {
      wx.closeBLEConnection({
        deviceId: this.data.deviceId
      });
    }
    this.setData({
      connected: false,
      connecting: false,
      discovering: false,
      deviceId: '',
      deviceName: '',
      serviceId: '',
      notifyCharacteristicId: '',
      writeCharacteristicId: '',
      receiveBuffer: '',
      statusText: '已断开连接'
    });
  },

  arrayBufferToString: function(buffer) {
    var bytes = new Uint8Array(buffer);
    var encoded = '';
    var i;
    for (i = 0; i < bytes.length; i++) {
      encoded += '%' + ('00' + bytes[i].toString(16)).slice(-2);
    }
    try {
      return decodeURIComponent(encoded);
    } catch (err) {
      var text = '';
      for (i = 0; i < bytes.length; i++) {
        text += String.fromCharCode(bytes[i]);
      }
      return text;
    }
  },

  stringToArrayBuffer: function(text) {
    var encoded = unescape(encodeURIComponent(text));
    var buffer = new ArrayBuffer(encoded.length);
    var bytes = new Uint8Array(buffer);
    var i;
    for (i = 0; i < encoded.length; i++) {
      bytes[i] = encoded.charCodeAt(i);
    }
    return buffer;
  }
});