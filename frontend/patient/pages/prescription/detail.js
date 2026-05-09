const api = require('../../utils/request.js');
var format = require('../../utils/format.js');

Page({
  data: {
    prescriptionId: null,
    prescription: {},
    statusText: {
      'pending': '待审核',
      'approved': '已通过',
      'rejected': '已拒绝'
    }
  },

  onLoad: function(options) {
    if (options.id) {
      this.setData({ prescriptionId: options.id });
      this.loadPrescriptionDetail();
    }
  },

  loadPrescriptionDetail: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    api.get('/prescriptions/' + this.data.prescriptionId, {}, { priority: 'critical' }).then(function(prescription) {
      prescription = self.normalizePrescription(prescription || {});
      self.setData({ prescription: prescription });
      wx.hideLoading();
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
      setTimeout(function() {
        wx.navigateBack();
      }, 1500);
    });
  },

  normalizePrescription: function(prescription) {
    prescription.created_at = format.formatDateTime(prescription.created_at);
    prescription.valid_until = format.formatDate(prescription.valid_until);
    prescription.audit_time = format.formatDateTime(prescription.audit_time);
    return prescription;
  },

  chatWithDoctor: function() {
    if (this.data.prescription.doctor) {
      wx.navigateTo({
        url: '/pages/consultation/chat?doctorId=' + this.data.prescription.doctor.id
      });
    }
  },

  usePrescription: function() {
    wx.setStorageSync('selected_prescription_id', this.data.prescriptionId);
    wx.switchTab({
      url: '/pages/shop/list'
    });
  }
});
