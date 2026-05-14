Page({
  data: {
    
  },

  onLoad: function(options) {
    
  },

  // 复制邮箱
  copyEmail: function() {
    wx.setClipboardData({
      data: 'support@health.com',
      success: function() {
        wx.showToast({
          title: '邮箱已复制',
          icon: 'success'
        });
      }
    });
  },

  // 复制电话
  copyPhone: function() {
    wx.setClipboardData({
      data: '400-888-8888',
      success: function() {
        wx.showToast({
          title: '电话已复制',
          icon: 'success'
        });
        
        // 询问是否拨打电话
        wx.showModal({
          title: '拨打电话',
          content: '是否拨打客服电话 400-888-8888？',
          confirmText: '拨打',
          success: function(res) {
            if (res.confirm) {
              wx.makePhoneCall({
                phoneNumber: '4008888888'
              });
            }
          }
        });
      }
    });
  },

  // 查看隐私政策
  viewPrivacy: function() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    });
  },

  // 查看用户协议
  viewTerms: function() {
    wx.navigateTo({
      url: '/pages/agreement/agreement'
    });
  }
});
