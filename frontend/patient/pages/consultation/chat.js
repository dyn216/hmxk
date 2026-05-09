var api = require('../../utils/request.js');
var format = require('../../utils/format.js');

Page({
  data: {
    consultationId: null,
    doctorId: null,
    doctor: {},
    messages: [],
    inputText: '',
    currentUserId: null,
    myAvatar: '',
    scrollToView: '',
    timer: null,
    sending: false,
    showActions: false
  },

  onLoad: function(options) {
    if (options.consultationId) {
      this.setData({ consultationId: options.consultationId });
    }
    if (options.doctorId) {
      this.setData({ doctorId: options.doctorId });
    }
    
    this.getCurrentUser();
    this.loadDoctorInfo();
    this.loadMessages();
    
    // 定时刷新消息
    var self = this;
    this.setData({
      timer: setInterval(function() {
        self.loadMessages(true);
      }, 3000)
    });
  },

  onUnload: function() {
    if (this.data.timer) {
      clearInterval(this.data.timer);
    }
  },

  getCurrentUser: function() {
    var self = this;
    api.get('/profile', {}, { priority: 'critical', silent: true }).then(function(profile) {
      self.setData({
        currentUserId: profile.user.id,
        myAvatar: profile.user.avatar
      });
      if (self.data.messages.length) {
        self.setData({
          messages: self.normalizeMessages(self.data.messages)
        });
      }
    }).catch(function(err) {
      console.error('获取用户信息失败:', err);
    });
  },

  loadDoctorInfo: function() {
    if (!this.data.doctorId) return;

    var self = this;
    api.get('/doctor/profile?doctor_id=' + this.data.doctorId, {}, { priority: 'critical', silent: true }).then(function(doctor) {
      self.setData({
        doctor: {
          id: doctor.id,
          name: doctor.name || (doctor.user ? doctor.user.name : ''),
          avatar: doctor.avatar || (doctor.user ? doctor.user.avatar : ''),
          title: doctor.title || (doctor.profile ? doctor.profile.title : ''),
          department: doctor.department || (doctor.profile ? doctor.profile.department : '')
        }
      });
    }).catch(function(err) {
      console.error('加载医生信息失败:', err);
    });
  },

  loadMessages: function(silent) {
    silent = silent === true;
    var self = this;
    if (!silent) {
      wx.showLoading({ title: '加载中...' });
    }

    var params = {};
    if (this.data.doctorId) {
      params.doctor_id = this.data.doctorId;
    }

    return api.get('/messages', params, { priority: 'critical', silent: silent }).then(function(messages) {
      messages = self.normalizeMessages((messages || []).slice().reverse());
      self.setData({
        messages: messages,
        scrollToView: messages.length > 0 ? 'msg-' + messages[messages.length - 1].id : ''
      });

      // 标记消息为已读
      self.markAsRead();
      if (!silent) {
        wx.hideLoading();
      }
    }).catch(function(err) {
      if (!silent) {
        wx.hideLoading();
        wx.showToast({ title: err.message || '加载失败', icon: 'none' });
      }
    });
  },

  markAsRead: function() {
    var self = this;
    var unreadMessages = this.data.messages.filter(function(msg) {
      return msg.receiver_id === self.data.currentUserId && !msg.is_read;
    });

    return Promise.all(unreadMessages.map(function(msg) {
      return api.put('/messages/' + msg.id + '/read', {}, { silent: true });
    })).catch(function(err) {
      console.error('标记已读失败:', err);
    });
  },

  onInput: function(e) {
    this.setData({
      inputText: e.detail.value,
      showActions: false
    });
  },

  sendMessage: function() {
    if (this.data.sending) return;
    var content = (this.data.inputText || '').trim();
    if (!content) {
      wx.showToast({ title: '请输入消息内容', icon: 'none' });
      return;
    }

    if (!this.data.doctorId) {
      wx.showToast({ title: '医生信息错误', icon: 'none' });
      return;
    }

    var self = this;
    this.setData({
      sending: true,
      showActions: false
    });
    api.post('/messages', {
        doctor_id: this.data.doctorId,
        content: content,
        message_type: 'text'
      }, { priority: 'critical' }).then(function(message) {
      if (message) {
        message.isMine = true;
      }
      message = self.normalizeMessage(message || {
        id: Date.now(),
        sender_id: self.data.currentUserId,
        content: content,
        message_type: 'text',
        created_at: self.formatTime(new Date())
      });
      self.setData({
        messages: self.data.messages.concat([message]),
        inputText: '',
        sending: false,
        scrollToView: 'msg-' + message.id
      });
    }).catch(function(err) {
      self.setData({ sending: false });
      wx.showToast({ title: err.message || '发送失败', icon: 'none' });
    });
  },

  normalizeMessages: function(messages) {
    var self = this;
    return (messages || []).map(function(message) {
      return self.normalizeMessage(message);
    });
  },

  normalizeMessage: function(message) {
    var createdAt = message.created_at || '';
    if (createdAt && typeof createdAt === 'string') {
      createdAt = this.formatMessageTime(createdAt);
    }
    return {
      id: message.id || Date.now(),
      sender_id: message.sender_id,
      receiver_id: message.receiver_id,
      content: message.content || '',
      message_type: message.message_type || 'text',
      is_read: message.is_read,
      created_at: createdAt || this.formatTime(new Date()),
      localImage: message.localImage || '',
      isMine: message.isMine === true || message.sender_id === this.data.currentUserId
    };
  },

  formatTime: function(date) {
    var hours = date.getHours();
    var minutes = date.getMinutes();
    if (hours < 10) hours = '0' + hours;
    if (minutes < 10) minutes = '0' + minutes;
    return hours + ':' + minutes;
  },

  formatMessageTime: function(value) {
    return format.formatTime(value);
  },

  chooseImage: function() {
    var self = this;
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: function(res) {
        var tempFilePaths = res.tempFilePaths || [];
        if (!tempFilePaths.length) return;
        var message = self.normalizeMessage({
          id: Date.now(),
          sender_id: self.data.currentUserId,
          content: '[图片]',
          message_type: 'image',
          localImage: tempFilePaths[0],
          created_at: self.formatTime(new Date()),
          isMine: true
        });
        self.setData({
          messages: self.data.messages.concat([message]),
          scrollToView: 'msg-' + message.id,
          showActions: false
        });
      }
    });
  },

  toggleMoreActions: function() {
    this.setData({
      showActions: !this.data.showActions
    });
  },

  showMoreTip: function() {
    this.setData({ showActions: false });
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    });
  }
});
