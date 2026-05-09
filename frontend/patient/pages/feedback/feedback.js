Page({
  data: {
    types: ['功能建议', 'Bug反馈', '使用问题', '其他'],
    typeIndex: 0,
    content: '',
    contact: ''
  },
  
  onTypeChange(e) {
    this.setData({ typeIndex: e.detail.value });
  },
  
  onContentInput(e) {
    this.setData({ content: e.detail.value });
  },
  
  onContactInput(e) {
    this.setData({ contact: e.detail.value });
  },
  
  submit() {
    if (!this.data.content.trim()) {
      wx.showToast({
        title: '请输入反馈内容',
        icon: 'none'
      });
      return;
    }
    
    // 保存反馈
    const feedback = {
      type: this.data.types[this.data.typeIndex],
      content: this.data.content,
      contact: this.data.contact,
      time: new Date().toLocaleString()
    };
    
    wx.showToast({
      title: '提交成功',
      icon: 'success'
    });
    
    setTimeout(function() {
      wx.navigateBack();
    }, 1500);
  }
});
