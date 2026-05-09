const api = require('../../utils/request.js');
const cache = require('../../utils/cache.js');
var format = require('../../utils/format.js');

Page({
  data: {
    prescriptions: [],
    statusText: {
      'pending': '待审核',
      'approved': '已通过',
      'rejected': '已拒绝'
    }
  },

  onLoad: function() {
  },

  onShow: function() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 3 });
    }
    this.loadPrescriptions();
  },

  loadPrescriptions: function() {
    const cacheKey = 'prescriptions:list';
    const self = this;
    return new Promise(function(resolve) {
      cache.swr({
        key: cacheKey,
        ttl: 30000,
        persist: true,
        fetcher: function() {
          return api.get('/prescriptions', {}, { priority: 'critical', silent: true });
        },
        onCache: function(prescriptions) {
          self.setData({ prescriptions: self.normalizePrescriptions(prescriptions) });
        },
        onFresh: function(prescriptions) {
          self.setData({ prescriptions: self.normalizePrescriptions(prescriptions) });
          resolve();
        },
        onError: function(err) {
          if (cache.get(cacheKey) === undefined) {
            wx.showToast({ title: err.message || '加载失败', icon: 'none' });
          }
          resolve();
        }
      });
      if (cache.get(cacheKey) !== undefined) resolve();
    });
  },

  normalizePrescriptions: function(prescriptions) {
    return (prescriptions || []).map(function(item) {
      item.created_at = format.formatDateTime(item.created_at);
      item.valid_until = format.formatDate(item.valid_until);
      return item;
    });
  },

  viewDetail: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/prescription/detail?id=' + id
    });
  },

  usePrescription: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.setStorageSync('selected_prescription_id', id);
    wx.switchTab({
      url: '/pages/shop/list'
    });
  },

  goToConsult: function() {
    wx.navigateTo({
      url: '/pages/doctor/doctor'
    });
  },

  onPullDownRefresh: function() {
    cache.clear('prescriptions:list');
    this.loadPrescriptions().then(function() {
      wx.stopPullDownRefresh();
    });
  }
});
