var RECORDS_KEY = 'bloodPressureRecords';
var patientApi = require('../../api/patient.js');
var auth = require('../../utils/auth.js');
var cache = require('../../utils/cache.js');

Page({
  data: {
    updateTime: '10:30',
    greeting: '今日',
    // 输入数据
    inputSystolic: '',
    inputDiastolic: '',
    inputHeartRate: '',
    // 实时提示
    showTip: false,
    tipStatus: '',
    tipIcon: '',
    tipTitle: '',
    tipDesc: '',
    // 健康数据
    systolic: 120,
    diastolic: 80,
    bpStatus: 'normal',
    bloodSugar: 5.8,
    bsStatus: 'normal',
    heartRate: 85,
    hrStatus: 'warn',
    weight: 65.5,
    weightStatus: 'normal',
    // 在线医生
    onlineDoctors: [],
    // 今日提醒
    todayReminders: [
      {
        id: 1,
        title: '早餐后服药',
        time: '08:00',
        content: '阿司匹林 x1',
        done: true
      },
      {
        id: 2,
        title: '测量晚间血压',
        time: '20:00',
        content: '建议静坐5分钟后测量',
        done: false
      }
    ]
  },

  onLoad: function () {
    this.getCurrentTime();
    this.loadUserData();
  },

  onShow: function() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
    this.getCurrentTime();
    this.loadUserData();
  },

  loadUserData: function() {
    var self = this;
    if (!auth.isLoggedIn()) {
      wx.showModal({
        title: '提示',
        content: '请先登录',
        showCancel: false,
        success: function() {
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      });
      return;
    }

    // 先把缓存渲染上屏（无网络等待），再后台 revalidate
    cache.swr({
      key: 'home:bundle',
      ttl: 30000,
      persist: true,
      fetcher: function() {
        return Promise.all([
          patientApi.getProfile({ priority: 'critical', silent: true }).catch(function() { return null; }),
          patientApi.getMeasurements({ type: 'bp', limit: 1 }, { priority: 'critical', silent: true }).catch(function() { return null; }),
          patientApi.getMeasurements({ type: 'hr', limit: 1 }, { priority: 'critical', silent: true }).catch(function() { return null; }),
          patientApi.getMedications({ priority: 'critical', silent: true }).catch(function() { return []; }),
          patientApi.getDoctors({ limit: 3 }, { priority: 'critical', silent: true }).catch(function() { return []; })
        ]).then(function(results) {
          return {
            profile: results[0],
            bpMeasurements: results[1],
            hrMeasurements: results[2],
            medications: results[3],
            doctors: results[4]
          };
        });
      },
      onCache: function(data) {
        self._applyHomeData(data);
      },
      onFresh: function(data) {
        self._applyHomeData(data);
      }
    });
  },

  _applyHomeData: function(data) {
    if (!data) return;
    var bpMeasurements = data.bpMeasurements || data.measurements;
    var hrMeasurements = data.hrMeasurements;
    var medications = data.medications;
    var doctors = data.doctors;

    if (bpMeasurements && bpMeasurements.length > 0) {
      var latest = bpMeasurements[0];
      var latestSystolic = latest.value1 || 120;
      var latestDiastolic = latest.value2 || 80;
      this.setData({
        systolic: latestSystolic,
        diastolic: latestDiastolic,
        bpStatus: this.getBpStatus(latestSystolic, latestDiastolic)
      });
    }

    if (hrMeasurements && hrMeasurements.length > 0) {
      var latestHr = hrMeasurements[0].value1 || 85;
      this.setData({
        heartRate: latestHr,
        hrStatus: this.getHrStatus(latestHr)
      });
    }

    if (medications) {
      var todayMeds = medications.filter(function(med) { return !med.end_date; }).slice(0, 2);
      if (todayMeds.length > 0) {
        this.setData({
          todayReminders: todayMeds.map(function(med) {
            var reminderTimes = [];
            try {
              reminderTimes = med.reminder_times ? JSON.parse(med.reminder_times) : [];
            } catch (e) {
              reminderTimes = [];
            }
            return {
              id: med.id,
              title: '服药提醒',
              time: reminderTimes[0] || '08:00',
              content: med.drug_name + ' x' + (med.dosage || ''),
              done: false
            };
          })
        });
      }
    }

    if (doctors && doctors.length) {
      this.setData({
        onlineDoctors: this._normalizeDoctors(doctors)
      });
    }
  },

  _normalizeDoctors: function(data) {
    var result = [];
    var i;
    for (i = 0; i < data.length; i++) {
      var doctor = data[i] || {};
      var user = doctor.user || {};
      var profile = doctor.profile || {};
      result.push({
        id: doctor.id || profile.id || doctor.doctor_id,
        name: this._cleanDoctorText(doctor.name || user.name, '医生'),
        title: this._cleanDoctorText(doctor.title || profile.title, '医生'),
        department: this._cleanDoctorText(doctor.department || profile.department, '慢病管理'),
        specialty: this._cleanDoctorText(doctor.specialty || doctor.introduction || profile.introduction, '慢性病健康管理'),
        online: doctor.online !== false,
        can_video: doctor.can_video !== false
      });
    }
    return result;
  },

  _cleanDoctorText: function(value, fallback) {
    value = value === undefined || value === null ? '' : String(value).trim();
    if (!value || value === '1') return fallback;
    return value;
  },

  getBpStatus: function(systolic, diastolic) {
    if (systolic < 90 || diastolic < 60) return 'low';
    if (systolic >= 140 || diastolic >= 90) return 'high';
    if (systolic >= 125 || diastolic >= 85) return 'elevated';
    return 'normal';
  },

  getHrStatus: function(heartRate) {
    if (heartRate < 60 || heartRate > 100) return 'warn';
    return 'normal';
  },

  getCurrentTime: function() {
    var now = new Date();
    var hour = now.getHours();
    var minute = now.getMinutes();
    var greeting = '今日';
    if (hour < 6) greeting = '夜深了';
    else if (hour < 11) greeting = '早安';
    else if (hour < 14) greeting = '中午好';
    else if (hour < 18) greeting = '下午好';
    else greeting = '晚上好';
    this.setData({
      updateTime: hour + ':' + (minute < 10 ? '0' + minute : minute),
      greeting
    });
  },

  // 输入处理
  onSystolicInput: function(e) {
    this.setData({
      inputSystolic: e.detail.value
    });
    this.checkBloodPressure();
  },

  onDiastolicInput: function(e) {
    this.setData({
      inputDiastolic: e.detail.value
    });
    this.checkBloodPressure();
  },

  onHeartRateInput: function(e) {
    this.setData({
      inputHeartRate: e.detail.value
    });
  },

  // 实时检查血压
  checkBloodPressure: function() {
    var inputSystolic = this.data.inputSystolic;
    var inputDiastolic = this.data.inputDiastolic;
    
    if (!inputSystolic || !inputDiastolic) {
      this.setData({ showTip: false });
      return;
    }

    var sys = Number(inputSystolic);
    var dia = Number(inputDiastolic);

    if (!isFinite(sys) || !isFinite(dia) || sys <= 0 || dia <= 0) {
      this.setData({ showTip: false });
      return;
    }

    this.setData(this.getBpTipData(sys, dia));
  },

  getBpTipData: function(systolic, diastolic) {
    var status = this.getBpStatus(systolic, diastolic);
    if (status === 'low') {
      return {
        showTip: true,
        tipStatus: 'tip-warning',
        tipIcon: '⚡',
        tipTitle: '血压偏低，注意补充营养，避免突然起身，如有不适请就医',
        tipDesc: ''
      };
    }
    if (status === 'high') {
      return {
        showTip: true,
        tipStatus: 'tip-danger',
        tipIcon: '⚠️',
        tipTitle: '血压偏高，建议减少盐分摄入，增加运动，必要时咨询医生',
        tipDesc: ''
      };
    }
    if (status === 'elevated') {
      return {
        showTip: true,
        tipStatus: 'tip-warning',
        tipIcon: '💡',
        tipTitle: '血压稍高，注意饮食和作息，建议多测量观察',
        tipDesc: ''
      };
    }
    return {
      showTip: true,
      tipStatus: 'tip-normal',
      tipIcon: '✅',
      tipTitle: '血压正常，继续保持健康的生活方式',
      tipDesc: ''
    };
  },

  saveData: function() {
    var values = this.validateQuickRecord();
    if (!values) {
      return;
    }

    var systolic = values.systolic;
    var diastolic = values.diastolic;
    var heartRate = values.heartRate;

    wx.showLoading({ title: '保存中...' });

    var self = this;
    patientApi.createMeasurement({
      type: 'bp',
      value1: systolic,
      value2: diastolic,
      measured_at: new Date().toISOString(),
      notes: '心率 ' + heartRate
    }).then(function(result) {
      wx.hideLoading();
      
      self.setData({
        systolic: systolic,
        diastolic: diastolic,
        heartRate: heartRate,
        bpStatus: self.getBpStatus(systolic, diastolic),
        inputSystolic: '',
        inputDiastolic: '',
        inputHeartRate: '',
        showTip: false
      });

      self.getCurrentTime();

      wx.showToast({
        title: '保存成功',
        icon: 'success'
      });

      var record = {
        id: Date.now(),
        measuredAt: Date.now(),
        date: new Date().toLocaleDateString('zh-CN').replace(/\//g, '-'),
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        systolic: systolic,
        diastolic: diastolic,
        heartRate: heartRate,
        status: self.getBpStatus(systolic, diastolic),
        statusText: self.getBpStatusText(self.getBpStatus(systolic, diastolic))
      };
      var records = wx.getStorageSync(RECORDS_KEY) || [];
      records.unshift(record);
      wx.setStorageSync(RECORDS_KEY, records);
    }).catch(function(error) {
      wx.hideLoading();
      console.error('保存失败:', error);
      wx.showToast({
        title: '保存失败，请重试',
        icon: 'none'
      });
    });
  },

  validateQuickRecord: function() {
    var inputSystolic = String(this.data.inputSystolic || '').trim();
    var inputDiastolic = String(this.data.inputDiastolic || '').trim();
    var inputHeartRate = String(this.data.inputHeartRate || '').trim();

    if (!inputSystolic || !inputDiastolic || !inputHeartRate) {
      wx.showToast({ title: '请填写完整数据', icon: 'none' });
      return null;
    }

    var systolic = Number(inputSystolic);
    var diastolic = Number(inputDiastolic);
    var heartRate = Number(inputHeartRate);

    if (!isFinite(systolic) || systolic < 60 || systolic > 250) {
      wx.showToast({ title: '请输入60-250之间的有效收缩压', icon: 'none' });
      return null;
    }
    if (!isFinite(diastolic) || diastolic < 40 || diastolic > 150) {
      wx.showToast({ title: '请输入40-150之间的有效舒张压', icon: 'none' });
      return null;
    }
    if (!isFinite(heartRate) || heartRate < 40 || heartRate > 200) {
      wx.showToast({ title: '请输入40-200之间的有效心率', icon: 'none' });
      return null;
    }

    return {
      systolic: Math.round(systolic),
      diastolic: Math.round(diastolic),
      heartRate: Math.round(heartRate)
    };
  },

  getBpStatusText: function(status) {
    if (status === 'high') return '高血压';
    if (status === 'elevated') return '偏高';
    if (status === 'low') return '偏低';
    return '正常';
  },

  goToRecords: function() {
    wx.navigateTo({
      url: '/pages/records/records'
    });
  },

  goToAiDoctor: function() {
    wx.navigateTo({
      url: '/pages/ai-doctor/ai-doctor'
    });
  },

  goToMedication: function() {
    wx.navigateTo({
      url: '/pages/medication/medication'
    });
  },

  goToDevice: function() {
    wx.navigateTo({
      url: '/pages/device/device'
    });
  },

  goToDoctor: function() {
    wx.navigateTo({
      url: '/pages/doctor/doctor'
    });
  },

  goToDetail: function(e) {
    var type = e.currentTarget.dataset.type;
    wx.navigateTo({
      url: '/pages/detail/detail?type=' + type
    });
  },

  viewDoctor: function(e) {
    var id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/doctor/doctor?id=' + id
    });
  },

  preventBubble: function() {
    // 阻止事件冒泡
  },

  chatWithDoctor: function(e) {
    var id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/consultation/chat?doctorId=' + id
    });
  },

  videoCallDoctor: function(e) {
    var id = e.currentTarget.dataset.id;
    var doctors = this.data.onlineDoctors || [];
    var doctor = null;
    var i;
    for (i = 0; i < doctors.length; i++) {
      if (String(doctors[i].id) === String(id)) {
        doctor = doctors[i];
        break;
      }
    }
    if (doctor && (!doctor.online || !doctor.can_video)) {
      wx.showToast({
        title: '医生当前不可视频',
        icon: 'none'
      });
      return;
    }
    wx.navigateTo({
      url: '/pages/video-call/video-call?doctorId=' + id
    });
  }
});