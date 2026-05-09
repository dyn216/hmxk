Page({
  data: {
    guardians: []
  },
  onLoad() {
    const guardians = wx.getStorageSync('guardians') || [];
    this.setData({ guardians });
  },
  addGuardian() {
    wx.showModal({
      title: '提示',
      content: '监护人添加功能开发中',
      showCancel: false
    });
  }
});