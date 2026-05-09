const api = require('../../utils/request.js');
var format = require('../../utils/format.js');

Page({
  data: {
    orderId: null,
    order: {},
    statusText: {
      'pending': '待支付',
      'paid': '待发货',
      'shipped': '待收货',
      'delivered': '待评价',
      'completed': '已完成',
      'cancelled': '已取消',
      'refunded': '已退款'
    }
  },

  onLoad: function(options) {
    if (options.id) {
      this.setData({ orderId: options.id });
      this.loadOrderDetail();
    }
  },

  loadOrderDetail: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    api.get('/shop/orders/' + this.data.orderId, {}, { priority: 'critical' }).then(function(order) {
      order = self.normalizeOrder(order || {});
      self.setData({ order: order });
      wx.hideLoading();
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
      setTimeout(function() {
        wx.navigateBack();
      }, 1500);
    });
  },

  normalizeOrder: function(order) {
    order.created_at = format.formatDateTime(order.created_at);
    order.paid_at = format.formatDateTime(order.paid_at);
    order.shipped_at = format.formatDateTime(order.shipped_at);
    order.delivered_at = format.formatDateTime(order.delivered_at);
    return order;
  },

  cancelOrder: function() {
    const self = this;
    wx.showModal({
      title: '取消订单',
      content: '确定要取消该订单吗？',
      success: function(res) {
        if (res.confirm) {
          api.put('/shop/orders/' + self.data.orderId + '/cancel', {}, { priority: 'critical' }).then(function() {
            wx.showToast({ title: '订单已取消', icon: 'success' });
            self.loadOrderDetail();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '取消失败', icon: 'none' });
          });
        }
      }
    });
  },

  payOrder: function() {
    const self = this;
    wx.showModal({
      title: '提示',
      content: '确认支付该订单？',
      success: function(res) {
        if (res.confirm) {
          api.put('/shop/orders/' + self.data.orderId + '/pay', {}, { priority: 'critical' }).then(function() {
            wx.showToast({ title: '支付成功', icon: 'success' });
            self.loadOrderDetail();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '支付失败', icon: 'none' });
          });
        }
      }
    });
  },

  confirmReceive: function() {
    const self = this;
    wx.showModal({
      title: '确认收货',
      content: '确认已收到商品？',
      success: function(res) {
        if (res.confirm) {
          api.put('/shop/orders/' + self.data.orderId + '/receive', {}, { priority: 'critical' }).then(function() {
            wx.showToast({ title: '确认成功', icon: 'success' });
            self.loadOrderDetail();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '操作失败', icon: 'none' });
          });
        }
      }
    });
  }
});
