Page({
  data: {
    chatName: '李华医生',
    timeLabel: '10:32',
    messages: [],
    inputText: '',
    scrollToView: '',
    showActions: false
  },
  
  onLoad: function(options) {
    // 获取参数
    var doctorName = options.doctorName;
    var patientName = options.patientName;
    this.setData({
      chatName: doctorName || patientName || '对话'
    });
    
    // 加载历史消息
    this.loadMessages();
  },
  
  loadMessages: function() {
    var mockMessages = [
      { 
        id: 1, 
        content: '您好，请问今天感觉怎么样？血压测量了吗？', 
        avatar: '医', 
        isMine: false, 
        time: '10:30' 
      },
      { 
        id: 2, 
        content: '医生你好，刚测了，120/80，感觉挺好的。', 
        avatar: '我', 
        isMine: true, 
        time: '10:31' 
      },
      { 
        id: 3, 
        content: '数值很稳定，继续保持清淡饮食。那个降压药还在按时吃吗？', 
        avatar: '医', 
        isMine: false, 
        time: '10:32' 
      }
    ];
    this.setData({ messages: mockMessages });
  },
  
  onInput: function(e) {
    this.setData({
      inputText: e.detail.value,
      showActions: false
    });
  },
  
  goBack: function() {
    var pages = getCurrentPages();
    if (pages.length > 1) {
      wx.navigateBack();
      return;
    }
    wx.switchTab({
      url: '/pages/index/index'
    });
  },
  
  sendMessage: function() {
    var content = (this.data.inputText || '').trim();
    if (!content) return;
    
    var newMsg = {
      id: Date.now(),
      content: content,
      avatar: '我',
      isMine: true,
      time: new Date().toLocaleTimeString().slice(0, 5)
    };
    
    this.setData({
      messages: this.data.messages.concat([newMsg]),
      inputText: '',
      scrollToView: 'msg' + newMsg.id,
      showActions: false
    });
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
        var newMsg = {
          id: Date.now(),
          content: '[图片]',
          image: tempFilePaths[0],
          avatar: '我',
          isMine: true,
          time: new Date().toLocaleTimeString().slice(0, 5)
        };
        self.setData({
          messages: self.data.messages.concat([newMsg]),
          scrollToView: 'msg' + newMsg.id,
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
