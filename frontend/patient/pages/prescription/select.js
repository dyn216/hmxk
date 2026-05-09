const api = require('../../utils/request.js');
var format = require('../../utils/format.js');

Page({
  data: {
    availablePrescriptions: [],
    selectedId: null,
    fromPage: ''
  },

  onLoad: function(options) {
    if (options.from) {
      this.setData({ fromPage: options.from });
    }
    this.loadAvailablePrescriptions();
  },

  loadAvailablePrescriptions: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    api.get('/prescriptions', {
        status: 'approved'
      }, { priority: 'critical' }).then(function(prescriptions) {
      // 筛选有效期内的处方
      const now = new Date();
      const available = (prescriptions || []).filter(function(p) {
        if (!p.valid_until) return true;
        return new Date(p.valid_until) > now;
      }).map(function(item) {
        item.created_at = format.formatDateTime(item.created_at);
        item.valid_until = format.formatDate(item.valid_until);
        return item;
      });
      
      self.setData({ availablePrescriptions: available });
      wx.hideLoading();
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    });
  },

  selectPrescription: function(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({ 
      selectedId: this.data.selectedId === id ? null : id 
    });
  },

  confirmSelection: function() {
    if (!this.data.selectedId) {
      wx.showToast({ title: '请选择处方', icon: 'none' });
      return;
    }

    const prescription = this.findPrescription(this.data.selectedId);

    if (this.data.fromPage === 'order') {
      // 从订单确认页面来的，返回并传递处方信息
      const pages = getCurrentPages();
      const prevPage = pages[pages.length - 2];
      if (prevPage) {
        prevPage.setData({ selectedPrescription: prescription });
      }
      wx.navigateBack();
    } else {
      // 其他情况，跳转到药品列表
      wx.setStorageSync('selected_prescription_id', this.data.selectedId);
      wx.switchTab({
        url: '/pages/shop/list'
      });
    }
  },

  findPrescription: function(id) {
    for (let i = 0; i < this.data.availablePrescriptions.length; i++) {
      if (this.data.availablePrescriptions[i].id === id) return this.data.availablePrescriptions[i];
    }
    return null;
  },

  goToConsult: function() {
    wx.navigateTo({
      url: '/pages/doctor/doctor'
    });
  }
});
