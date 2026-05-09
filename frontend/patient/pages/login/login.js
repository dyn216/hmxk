const auth = require('../../utils/auth.js');

Page({
  data: {
    phone: '13900000001',
    password: 'patient123',
    showPassword: false,
    loading: false
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

  handleLogin: function() {
    const phone = this.data.phone;
    const password = this.data.password;
    const self = this;

    if (!phone || phone.length !== 11) {
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
