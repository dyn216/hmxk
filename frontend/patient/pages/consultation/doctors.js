Page({
  onLoad: function(options) {
    this.redirectToDoctor(options || {});
  },

  redirectToDoctor: function(options) {
    var url = '/pages/doctor/doctor';
    if (options.id) {
      url += '?id=' + encodeURIComponent(options.id);
    }
    wx.redirectTo({
      url: url,
      fail: function() {
        wx.navigateTo({ url: url });
      }
    });
  }
});
