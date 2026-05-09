const RECORDS_KEY = 'bloodPressureRecords';

Page({
  data: {
    totalRecords: 0,
    avgSystolic: 0,
    avgDiastolic: 0
  },

  onLoad: function (options) {
    this.loadRecords();
  },

  loadRecords: function() {
    const records = wx.getStorageSync(RECORDS_KEY) || [];
    const total = records.length;
    let avgSystolic = 0;
    let avgDiastolic = 0;
    if (total > 0) {
      avgSystolic = Math.round(records.reduce(function(sum, item) { return sum + item.systolic; }, 0) / total);
      avgDiastolic = Math.round(records.reduce(function(sum, item) { return sum + item.diastolic; }, 0) / total);
    }
    this.setData({
      totalRecords: total,
      avgSystolic: avgSystolic,
      avgDiastolic: avgDiastolic
    });
  }
});