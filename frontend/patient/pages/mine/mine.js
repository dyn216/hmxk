const RECORDS_KEY = 'bloodPressureRecords';

Page({
  data: {
    totalRecords: 0,
    avgSystolic: 0
  },

  onLoad: function (options) {
    this.loadRecords();
  },

  loadRecords: function() {
    const records = wx.getStorageSync(RECORDS_KEY) || [];
    const total = records.length;
    let avgSystolic = 0;
    if (total > 0) {
      avgSystolic = Math.round(records.reduce(function(sum, item) { return sum + item.systolic; }, 0) / total);
    }
    this.setData({
      totalRecords: total,
      avgSystolic: avgSystolic
    });
  },

  // 跳转监护人绑定
  goToGuardian: function() {
    wx.navigateTo({
      url: '/pages/guardian/guardian'
    });
  },

  // 跳转用药管理
  goToMedication: function() {
    wx.navigateTo({
      url: '/pages/medication/medication'
    });
  },

  // 跳转手环设备
  goToDevice: function() {
    wx.navigateTo({
      url: '/pages/device/device'
    });
  },

  // 跳转系统设置
  goToSetting: function() {
    wx.navigateTo({
      url: '/pages/setting/setting'
    });
  },

  // 其他菜单（功能开发中）
  goToSecurity: function() {
    wx.navigateTo({
      url: '/pages/security/security'
    });
  },

  goToUpgrade: function() {
    wx.showToast({
      title: '系统升级功能开发中',
      icon: 'none'
    });
  },

  goToAbout: function() {
    wx.navigateTo({
      url: '/pages/about/about'
    });
  },

  goToService: function() {
    wx.navigateTo({
      url: '/pages/service/service'
    });
  }
});