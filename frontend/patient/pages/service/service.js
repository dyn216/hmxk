Page({
  data: {
    faqList: [
      {
        id: 1,
        question: '如何绑定智能设备？',
        answer: '进入"手环"页面，点击右上角"+"按钮，按照提示打开蓝牙并靠近设备即可自动配对。'
      },
      {
        id: 2,
        question: '如何查看历史监测数据？',
        answer: '进入"记录"页面，可以查看所有历史监测数据，支持按日期和类型筛选。'
      },
      {
        id: 3,
        question: '用药提醒如何设置？',
        answer: '进入"我的"->"用药管理"，点击"添加用药"，填写药品信息和提醒时间即可。'
      },
      {
        id: 4,
        question: '监护人如何查看我的数据？',
        answer: '进入"我的"->"监护人绑定"，添加监护人手机号并授权后，监护人即可查看您的健康数据。'
      },
      {
        id: 5,
        question: '如何联系医生？',
        answer: '进入"医生"页面，可以查看签约医生信息，点击即可发起咨询或预约视频问诊。'
      },
      {
        id: 6,
        question: '数据安全吗？',
        answer: '我们采用银行级加密技术保护您的数据，所有数据传输都经过加密处理，绝对安全可靠。'
      }
    ]
  },

  onLoad: function(options) {
    
  },

  // 电话咨询
  callService: function() {
    wx.showModal({
      title: '拨打客服电话',
      content: '客服热线：400-888-8888\n工作时间：周一至周日 9:00-18:00',
      confirmText: '拨打',
      success: function(res) {
        if (res.confirm) {
          wx.makePhoneCall({
            phoneNumber: '4008888888',
            fail: function(err) {
              wx.showToast({
                title: '拨打失败',
                icon: 'none'
              });
            }
          });
        }
      }
    });
  },

  // 在线客服
  onlineChat: function() {
    wx.showToast({
      title: '客服功能开发中',
      icon: 'none',
      duration: 2000
    });
    
    // TODO: 跳转到在线客服聊天页面
    // wx.navigateTo({
    //   url: '/pages/chat/chat'
    // });
  },

  // 查看常见问题
  viewFAQ: function() {
    wx.pageScrollTo({
      selector: '.faq-section',
      duration: 300
    });
  },

  // 意见反馈
  feedback: function() {
    wx.showModal({
      title: '意见反馈',
      content: '请输入您的意见或建议',
      editable: true,
      placeholderText: '请输入内容',
      success: function(res) {
        if (res.confirm && res.content) {
          // TODO: 提交反馈到后端
          wx.showToast({
            title: '感谢您的反馈',
            icon: 'success'
          });
        }
      }
    });
  },

  // 查看问题详情
  viewFaqDetail: function(e) {
    const item = e.currentTarget.dataset.item;
    wx.showModal({
      title: item.question,
      content: item.answer,
      confirmText: '我知道了',
      showCancel: false
    });
  },

  // 发送邮件
  sendEmail: function() {
    wx.setClipboardData({
      data: 'support@health.com',
      success: function() {
        wx.showToast({
          title: '邮箱已复制',
          icon: 'success',
          duration: 2000
        });
        
        wx.showModal({
          title: '提示',
          content: '邮箱地址已复制到剪贴板，请使用邮件应用发送邮件。',
          showCancel: false
        });
      }
    });
  }
});
