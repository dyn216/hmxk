var api = require('../../utils/request.js');

Page({
  data: {
    doctorInfo: {
      id: null,
      name: '',
      department: '',
      avatar: ''
    },
    consultationId: null,
    roomInfo: null,
    localPushUrl: '',
    remotePlayUrl: '',
    streamReady: false,
    isConnected: false,
    statusText: '正在建立视频问诊...',
    callDuration: '00:00',
    isMuted: false,
    isCameraOff: false,
    isSpeakerOn: true,
    mediaAuthorized: false,
    pusherBlocked: false,
    showMenu: false,
    callStartTime: null,
    durationTimer: null,
    pollTimer: null,
    ending: false,
    manualEnding: false
  },

  onLoad: function(options) {
    this.setData({
      'doctorInfo.id': options.doctorId || null,
      'doctorInfo.name': decodeURIComponent(options.doctorName || '') || '在线医生',
      'doctorInfo.department': decodeURIComponent(options.department || ''),
      consultationId: options.consultationId || null
    });
    this.ensureMediaPermission();
  },

  onUnload: function() {
    this.clearTimers();
    if (this.data.consultationId && !this.data.ending && !this.data.manualEnding) {
      this.endCall(true);
    }
  },

  createOrJoinCall: function() {
    var self = this;
    var data = {};
    if (this.data.consultationId) {
      data.consultation_id = parseInt(this.data.consultationId, 10);
    }
    if (this.data.doctorInfo.id) {
      data.doctor_id = parseInt(this.data.doctorInfo.id, 10);
    }
    wx.showLoading({ title: '连接中...' });
    api.post('/video-calls', data, { priority: 'critical' }).then(function(room) {
      wx.hideLoading();
      self.applyRoomInfo(room);
      self.startPolling();
    }).catch(function(err) {
      wx.hideLoading();
      self.setData({
        statusText: err.message || '视频问诊连接失败'
      });
      wx.showToast({
        title: err.message || '连接失败',
        icon: 'none'
      });
    });
  },

  ensureMediaPermission: function() {
    var self = this;
    wx.getSetting({
      success: function(res) {
        var auth = res.authSetting || {};
        if (auth['scope.camera'] && auth['scope.record']) {
          self.setData({ mediaAuthorized: true });
          self.createOrJoinCall();
          return;
        }
        self.requestMediaPermission();
      },
      fail: function() {
        self.requestMediaPermission();
      }
    });
  },

  requestMediaPermission: function() {
    var self = this;
    wx.authorize({
      scope: 'scope.camera',
      success: function() {
        wx.authorize({
          scope: 'scope.record',
          success: function() {
            self.setData({ mediaAuthorized: true });
            self.createOrJoinCall();
          },
          fail: function() {
            self.handleMediaPermissionDenied();
          }
        });
      },
      fail: function() {
        self.handleMediaPermissionDenied();
      }
    });
  },

  handleMediaPermissionDenied: function() {
    var self = this;
    this.setData({
      mediaAuthorized: false,
      statusText: '请允许摄像头和麦克风权限后重新进入视频问诊'
    });
    wx.showModal({
      title: '需要音视频权限',
      content: '视频问诊需要使用摄像头和麦克风。请在设置中允许后重新进入。',
      confirmText: '去设置',
      success: function(res) {
        if (!res.confirm) return;
        wx.openSetting({
          success: function(setting) {
            var auth = setting.authSetting || {};
            if (auth['scope.camera'] && auth['scope.record']) {
              self.setData({ mediaAuthorized: true });
              self.createOrJoinCall();
            } else {
              wx.showToast({
                title: '未获得音视频权限',
                icon: 'none'
              });
            }
          }
        });
      }
    });
  },

  applyRoomInfo: function(room) {
    room = room || {};
    console.log('video room', {
      role: room.role,
      local_push_url: room.local_push_url,
      remote_play_url: room.remote_play_url,
      stream_ready: room.stream_ready,
      status: room.status
    });
    var streamReady = room.stream_ready === true && !!room.local_push_url && !!room.remote_play_url;
    this.setData({
      consultationId: room.consultation_id || this.data.consultationId,
      roomInfo: room,
      localPushUrl: room.local_push_url || '',
      remotePlayUrl: room.remote_play_url || '',
      streamReady: streamReady,
      isConnected: room.status === 'ongoing',
      statusText: streamReady ? '视频问诊中' : '问诊房间已建立，等待音视频服务配置',
      'doctorInfo.id': room.doctor_id || this.data.doctorInfo.id,
      'doctorInfo.name': room.doctor_name || this.data.doctorInfo.name,
      'doctorInfo.department': room.department || this.data.doctorInfo.department
    });
    if (room.status === 'ongoing' && !this.data.durationTimer) {
      this.startDurationTimer(room.start_time);
    }
  },

  startPolling: function() {
    var self = this;
    if (this.data.pollTimer || !this.data.consultationId) return;
    this.setData({
      pollTimer: setInterval(function() {
        self.refreshRoom(true);
      }, 5000)
    });
  },

  refreshRoom: function(silent) {
    var self = this;
    if (!this.data.consultationId) return;
    api.get('/video-calls/' + this.data.consultationId, {}, { priority: 'normal', silent: silent === true }).then(function(room) {
      self.applyRoomInfo(room);
      if (room && (room.status === 'completed' || room.status === 'cancelled')) {
        self.clearTimers();
        self.setData({ statusText: '视频问诊已结束' });
      }
    }).catch(function() {});
  },

  startDurationTimer: function(startTime) {
    var self = this;
    var now = startTime ? new Date(startTime).getTime() : Date.now();
    if (isNaN(now)) {
      now = Date.now();
    }
    this.setData({ callStartTime: now });
    this.setData({
      durationTimer: setInterval(function() {
        var duration = Math.floor((Date.now() - now) / 1000);
        var minutes = Math.floor(duration / 60);
        var seconds = duration % 60;
        self.setData({
          callDuration: self.pad2(minutes) + ':' + self.pad2(seconds)
        });
      }, 1000)
    });
  },

  clearTimers: function() {
    if (this.data.durationTimer) {
      clearInterval(this.data.durationTimer);
    }
    if (this.data.pollTimer) {
      clearInterval(this.data.pollTimer);
    }
    this.setData({
      durationTimer: null,
      pollTimer: null
    });
  },

  pad2: function(value) {
    value = String(value);
    return value.length < 2 ? '0' + value : value;
  },

  toggleMic: function() {
    this.setData({
      isMuted: !this.data.isMuted
    });
    wx.showToast({
      title: this.data.isMuted ? '麦克风已静音' : '麦克风已开启',
      icon: 'none'
    });
  },

  toggleCamera: function() {
    this.setData({
      isCameraOff: !this.data.isCameraOff
    });
    wx.showToast({
      title: this.data.isCameraOff ? '摄像头已关闭' : '摄像头已开启',
      icon: 'none'
    });
  },

  toggleSpeaker: function() {
    this.setData({
      isSpeakerOn: !this.data.isSpeakerOn
    });
    wx.showToast({
      title: this.data.isSpeakerOn ? '已切换到扬声器' : '已切换到听筒',
      icon: 'none'
    });
  },

  showMore: function() {
    this.setData({
      showMenu: !this.data.showMenu
    });
  },

  onPusherStateChange: function(e) {
    console.log('live-pusher statechange', e.detail);
    if (e.detail && e.detail.code < 0) {
      wx.showToast({
        title: '推流异常 ' + e.detail.code,
        icon: 'none'
      });
    }
  },

  onPusherNetStatus: function(e) {
    console.log('live-pusher netstatus', e.detail);
  },

  onPusherError: function(e) {
    console.error('live-pusher error', e.detail);
    var detail = e.detail || {};
    if (detail.errno === 102 || detail.errMsg === 'fail:access denied') {
      this.handlePusherAccessDenied();
      return;
    }
    wx.showToast({
      title: '推流错误',
      icon: 'none'
    });
  },

  handlePusherAccessDenied: function() {
    this.setData({
      mediaAuthorized: false,
      pusherBlocked: true,
      statusText: '微信拒绝启动摄像头推流，请检查权限或小程序实时音视频能力'
    });
    wx.showModal({
      title: '无法启动视频推流',
      content: '如果摄像头和麦克风已允许，但仍提示 access denied，请检查小程序后台是否已开通 live-pusher/live-player 实时音视频能力，并使用真机预览或体验版测试。',
      confirmText: '知道了',
      showCancel: false
    });
  },

  onPlayerStateChange: function(e) {
    console.log('live-player statechange', e.detail);
    if (e.detail && e.detail.code < 0) {
      wx.showToast({
        title: '播放异常 ' + e.detail.code,
        icon: 'none'
      });
    }
  },

  onPlayerNetStatus: function(e) {
    console.log('live-player netstatus', e.detail);
  },

  sendMessage: function() {
    this.setData({ showMenu: false });
    wx.navigateTo({
      url: '/pages/consultation/chat?doctorId=' + encodeURIComponent(this.data.doctorInfo.id || '')
    });
  },

  hangUp: function() {
    var self = this;
    wx.showModal({
      title: '确认挂断',
      content: '确定要结束视频问诊吗？',
      confirmColor: '#f56c6c',
      success: function(res) {
        if (res.confirm) {
          self.endCall();
        }
      }
    });
  },

  endCall: function(silent) {
    var self = this;
    if (this.data.ending) return;
    silent = silent === true;
    this.setData({
      ending: true,
      manualEnding: !silent
    });
    this.clearTimers();
    if (!this.data.consultationId) {
      if (!silent) {
        this.finishLocalCall();
      }
      return;
    }
    api.put('/video-calls/' + this.data.consultationId + '/end', {
      duration: this.data.callDuration,
      notes: '患者端结束视频问诊'
    }, { priority: 'critical', silent: true }).then(function(room) {
      if (!silent) {
        self.applyRoomInfo(room);
        self.finishLocalCall();
      }
    }).catch(function() {
      if (!silent) {
        self.finishLocalCall();
      }
    });
  },

  finishLocalCall: function() {
    this.saveCallRecord();
    wx.showToast({
      title: '问诊已结束',
      icon: 'success',
      duration: 1200
    });
    setTimeout(function() {
      wx.navigateBack();
    }, 1200);
  },

  saveCallRecord: function() {
    var record = {
      id: Date.now(),
      consultationId: this.data.consultationId,
      doctorId: this.data.doctorInfo.id,
      doctorName: this.data.doctorInfo.name,
      department: this.data.doctorInfo.department,
      duration: this.data.callDuration,
      time: new Date().toLocaleString(),
      type: 'video'
    };
    var records = wx.getStorageSync('callRecords') || [];
    records.unshift(record);
    wx.setStorageSync('callRecords', records);
  }
});
