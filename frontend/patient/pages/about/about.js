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
    wx.showModal({
      title: '隐私政策',
      content: '我们重视您的隐私保护。您的个人信息和健康数据将被严格加密存储，不会在未经您同意的情况下分享给第三方。我们仅在提供服务所必需的范围内收集和使用您的信息。',
      confirmText: '我知道了',
      showCancel: false
    });
  },

  // 查看用户协议
  viewTerms: function() {
    wx.showModal({
      title: '用户协议',
      content: '使用本应用即表示您同意遵守我们的用户协议。本应用提供的健康建议仅供参考，不能替代专业医疗诊断和治疗。如有任何健康问题，请及时就医。',
      confirmText: '我知道了',
      showCancel: false
    });
  }
});
