const auth = require('../../utils/auth.js');

Page({
  data: {
    phone: '',
    password: '',
    showPassword: false,
    loading: false,
    agreedPrivacy: false
  },

  onLoad: function() {
    this.setData({
      agreedPrivacy: wx.getStorageSync('patient_privacy_agreed') === true
    });
  },

  onPhoneInput: function(e) {
    this.setData({
      phone: e.detail.value
    });
  },

  onPasswordInput: function(e) {
    this.setData({
      password: e.detail.value
    });
  },

  togglePassword: function() {
    this.setData({
      showPassword: !this.data.showPassword
    });
  },

  onAgreementChange: function(e) {
    this.setData({
      agreedPrivacy: e.detail.value.indexOf('agreed') !== -1
    });
  },

  openAgreement: function() {
    wx.navigateTo({
      url: '/pages/agreement/agreement'
    });
  },

  openPrivacy: function() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    });
  },

  handleLogin: function() {
    const phone = this.data.phone;
    const password = this.data.password;
    const self = this;

    if (!this.data.agreedPrivacy) {
      wx.showModal({
        title: '请先阅读并同意',
        content: '登录前请阅读并同意《用户服务协议》和《隐私政策》。我们会按照协议说明收集和使用您的手机号、账号信息及健康服务相关数据。',
        confirmText: '我知道了',
        showCancel: false
      });
      return;
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      });
      return;
    }

    if (!password) {
      wx.showToast({
        title: '请输入密码',
        icon: 'none'
      });
      return;
    }

    this.setData({ loading: true });

    auth.login(phone, password)
      .then(function() {
        wx.setStorageSync('patient_privacy_agreed', true);
        wx.showToast({
          title: '登录成功',
          icon: 'success'
        });

        setTimeout(function() {
          wx.reLaunch({
            url: '/pages/index/index',
            fail: function() {
              wx.switchTab({
                url: '/pages/index/index'
              });
            }
          });
        }, 1500);
      })
      .catch(function(error) {
        console.error('登录失败:', error);
        wx.showToast({
          title: error.message || '登录失败',
          icon: 'none'
        });
      })
      .then(function() {
        self.setData({ loading: false });
      }, function() {
        self.setData({ loading: false });
      });
  }
});
