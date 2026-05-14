var patientApi = require('../../api/patient.js');
var auth = require('../../utils/auth.js');

var AI_CONSENT_KEY = 'ai_doctor_consent';

var QUICK_QUESTIONS = [
  '我最近的血压趋势怎么样？',
  '今天的测量数据正常吗？',
  '我应该如何调整饮食？',
  '现在需要去医院吗？'
];

function formatTime(iso) {
  if (!iso) return '';
  var d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  var hh = d.getHours();
  var mm = d.getMinutes();
  return (hh < 10 ? '0' + hh : hh) + ':' + (mm < 10 ? '0' + mm : mm);
}

function buildView(msg) {
  return {
    id: msg.id,
    role: msg.role,
    content: msg.content,
    timeText: formatTime(msg.created_at),
    isMine: msg.role === 'user'
  };
}

Page({
  data: {
    messages: [],
    inputText: '',
    sending: false,
    loading: true,
    showConsent: false,
    quickQuestions: QUICK_QUESTIONS,
    scrollIntoView: '',
    disclaimer: 'AI 建议仅供日常健康参考，不能替代医生面诊。如有不适或紧急情况，请及时就医。'
  },

  onLoad: function () {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/login' });
      return;
    }
    var consent = wx.getStorageSync(AI_CONSENT_KEY);
    if (!consent) {
      this.setData({ showConsent: true, loading: false });
      return;
    }
    this.loadHistory();
  },

  loadHistory: function () {
    var self = this;
    self.setData({ loading: true });
    patientApi.getAiChatHistory({ silent: true }).then(function (res) {
      var list = (res && res.messages) || [];
      var views = list.map(buildView);
      var welcome = views.length ? null : {
        id: 'welcome',
        role: 'assistant',
        content: '您好，我是您的 AI 健康助手 MiMo。我可以根据您的健康档案、用药情况和最近的测量数据，给出个性化的健康建议。请问您今天想咨询什么？',
        timeText: '',
        isMine: false
      };
      self.setData({
        messages: welcome ? [welcome] : views,
        loading: false
      });
      self.scrollToBottom();
    }).catch(function () {
      self.setData({ loading: false });
    });
  },

  acceptConsent: function () {
    wx.setStorageSync(AI_CONSENT_KEY, '1');
    this.setData({ showConsent: false });
    this.loadHistory();
  },

  declineConsent: function () {
    wx.navigateBack({ delta: 1 });
  },

  openPrivacy: function () {
    wx.navigateTo({ url: '/pages/privacy/privacy' });
  },

  onInput: function (e) {
    this.setData({ inputText: e.detail.value });
  },

  pickQuickQuestion: function (e) {
    var text = e.currentTarget.dataset.text;
    if (!text || this.data.sending) return;
    this.sendText(text);
  },

  send: function () {
    if (this.data.sending) return;
    var text = String(this.data.inputText || '').trim();
    if (!text) {
      wx.showToast({ title: '请输入内容', icon: 'none' });
      return;
    }
    this.sendText(text);
  },

  sendText: function (text) {
    var self = this;
    var pendingId = 'pending_' + Date.now();
    var userView = {
      id: 'u_' + Date.now(),
      role: 'user',
      content: text,
      timeText: formatTime(new Date().toISOString()),
      isMine: true
    };
    var typingView = {
      id: pendingId,
      role: 'assistant',
      content: 'AI 正在思考…',
      timeText: '',
      isMine: false,
      pending: true
    };
    var nextMessages = self.data.messages.concat([userView, typingView]);
    self.setData({
      messages: nextMessages,
      inputText: '',
      sending: true
    });
    self.scrollToBottom();

    patientApi.sendAiChat(text).then(function (res) {
      var assistant = res && res.assistant_message;
      var userMsg = res && res.user_message;
      var msgs = self.data.messages.slice();
      // 替换 typing 占位
      msgs = msgs.filter(function (m) { return m.id !== pendingId; });
      // 替换临时 user view 为后端返回的真实 id
      if (userMsg) {
        msgs = msgs.map(function (m) {
          if (m.id === userView.id) return buildView(userMsg);
          return m;
        });
      }
      if (assistant) msgs.push(buildView(assistant));
      self.setData({ messages: msgs, sending: false });
      self.scrollToBottom();
    }).catch(function (err) {
      var msgs = self.data.messages.slice().filter(function (m) { return m.id !== pendingId; });
      msgs.push({
        id: 'err_' + Date.now(),
        role: 'assistant',
        content: (err && err.message) ? ('调用失败：' + err.message) : 'AI 服务暂不可用，请稍后再试。',
        timeText: formatTime(new Date().toISOString()),
        isMine: false,
        error: true
      });
      self.setData({ messages: msgs, sending: false });
      self.scrollToBottom();
    });
  },

  scrollToBottom: function () {
    var msgs = this.data.messages;
    if (!msgs.length) return;
    var last = msgs[msgs.length - 1];
    this.setData({ scrollIntoView: 'msg-' + last.id });
  },

  clearChat: function () {
    var self = this;
    wx.showModal({
      title: '清空对话',
      content: '将删除所有 AI 对话记录，确定继续？',
      success: function (res) {
        if (!res.confirm) return;
        patientApi.clearAiChat().then(function () {
          self.setData({ messages: [] });
          self.loadHistory();
          wx.showToast({ title: '已清空', icon: 'success' });
        });
      }
    });
  }
});
