Page({
  data: {
    measureRemind: true,
    medicationRemind: true,
    sportRemind: true
  },
  toggleMeasureRemind: function(e) {
    this.setData({ measureRemind: e.detail.value });
  },
  toggleMedicationRemind: function(e) {
    this.setData({ medicationRemind: e.detail.value });
  },
  toggleSportRemind: function(e) {
    this.setData({ sportRemind: e.detail.value });
  },
  exportData: function() {
    wx.showLoading({ title: '导出中...' });
    setTimeout(function() {
      wx.hideLoading();
      wx.showModal({
        title: '导出成功',
        content: '健康数据已导出到相册',
        showCancel: false
      });
    }, 1500);
  },
  clearCache: function() {
    wx.showModal({
      title: '清除缓存',
      content: '确定要清除所有缓存数据吗？',
      success: function(res) {
        if (res.confirm) {
          wx.clearStorageSync();
          wx.showToast({
            title: '缓存已清除',
            icon: 'success'
          });
        }
      }
    });
  },
  feedback: function() {
    wx.navigateTo({
      url: '/pages/feedback/feedback'
    });
  },
  privacy: function() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    });
  }
});