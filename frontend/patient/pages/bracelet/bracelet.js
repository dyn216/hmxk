Page({
  data: {
    battery: 85,
    vibration: false
  },
  toggleVibration(e) {
    this.setData({ vibration: e.detail.value });
  }
});