const RECORDS_KEY = 'bloodPressureRecords';
const api = require('../../utils/request.js');

Page({
  data: {
    totalRecords: 0,
    weeklyTotalRecords: 0,
    avgSystolic: 0,
    weeklyAvgSystolic: 0,
    avgDiastolic: 0,
    weeklyAvgDiastolic: 0,
    records: []
  },

  onLoad: function (options) {
    this.loadRecords();
  },

  loadRecords: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    return api.get('/measurements', { type: 'bp', days: 365, limit: 100 }, { priority: 'critical', silent: true }).then(function(list) {
      const records = (list || []).map(function(item) {
        return self.formatMeasurement(item);
      });
      wx.setStorageSync(RECORDS_KEY, records);
      self.applyRecords(records);
      wx.hideLoading();
    }).catch(function() {
      const records = wx.getStorageSync(RECORDS_KEY) || [];
      self.applyRecords(records);
      wx.hideLoading();
    });
  },

  applyRecords: function(records) {
    const total = records.length;
    const weekRecords = this.filterThisWeek(records);
    let avgSystolic = 0;
    let avgDiastolic = 0;
    let weeklyAvgSystolic = 0;
    let weeklyAvgDiastolic = 0;
    if (total > 0) {
      avgSystolic = Math.round(records.reduce(function(sum, item) { return sum + item.systolic; }, 0) / total);
      avgDiastolic = Math.round(records.reduce(function(sum, item) { return sum + item.diastolic; }, 0) / total);
    }
    if (weekRecords.length > 0) {
      weeklyAvgSystolic = Math.round(weekRecords.reduce(function(sum, item) { return sum + item.systolic; }, 0) / weekRecords.length);
      weeklyAvgDiastolic = Math.round(weekRecords.reduce(function(sum, item) { return sum + item.diastolic; }, 0) / weekRecords.length);
    }
    this.setData({
      totalRecords: total,
      weeklyTotalRecords: weekRecords.length,
      avgSystolic: avgSystolic,
      weeklyAvgSystolic: weeklyAvgSystolic,
      avgDiastolic: avgDiastolic,
      weeklyAvgDiastolic: weeklyAvgDiastolic,
      records: records
    });
  },

  formatMeasurement: function(item) {
    const measuredAt = item.measured_at ? new Date(item.measured_at) : new Date();
    const systolic = Math.round(item.value1 || 0);
    const diastolic = Math.round(item.value2 || 0);
    const status = this.getBpStatus(systolic, diastolic);
    return {
      id: item.id,
      measuredAt: measuredAt.getTime(),
      date: measuredAt.toLocaleDateString('zh-CN').replace(/\//g, '-'),
      time: measuredAt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      systolic: systolic,
      diastolic: diastolic,
      heartRate: this.parseHeartRate(item.notes),
      status: status,
      statusText: this.getStatusText(status),
      suggestion: item.ai_suggestion || ''
    };
  },

  filterThisWeek: function(records) {
    const now = new Date();
    const start = new Date(now);
    const day = start.getDay() || 7;
    start.setHours(0, 0, 0, 0);
    start.setDate(start.getDate() - day + 1);
    const startTime = start.getTime();
    const endTime = now.getTime();
    return records.filter(function(item) {
      const time = Number(item.measuredAt || 0);
      return time >= startTime && time <= endTime;
    });
  },

  parseHeartRate: function(notes) {
    const matched = String(notes || '').match(/心率\s*(\d+)/);
    return matched ? parseInt(matched[1]) : 0;
  },

  getBpStatus: function(systolic, diastolic) {
    if (systolic < 90 || diastolic < 60) return 'low';
    if (systolic >= 140 || diastolic >= 90) return 'high';
    if (systolic >= 125 || diastolic >= 85) return 'elevated';
    return 'normal';
  },

  getStatusText: function(status) {
    if (status === 'high') return '高血压';
    if (status === 'elevated') return '偏高';
    if (status === 'low') return '偏低';
    return '正常';
  },

  goToDetail: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/detail/detail?id=' + id
    });
  }
});