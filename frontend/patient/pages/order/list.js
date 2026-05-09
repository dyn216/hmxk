const api = require('../../utils/request.js');
const cache = require('../../utils/cache.js');

Page({
  data: {
    currentTab: 'all',
    orders: [],
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
    if (options.status) {
      this.setData({ currentTab: options.status });
    }
    this.loadOrders();
  },

  onShow: function() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
    this.loadOrders();
  },

  switchTab: function(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
    this.loadOrders();
  },

  loadOrders: function(showLoadingOnEmpty) {
    const tab = this.data.currentTab;
    const params = tab === 'all' ? {} : { status: tab };
    const cacheKey = 'orders:' + tab;
    const self = this;

    let didLoading = false;
    if (showLoadingOnEmpty && cache.get(cacheKey) === undefined) {
      wx.showLoading({ title: '加载中...', mask: false });
      didLoading = true;
    }

    return new Promise(function(resolve) {
      cache.swr({
        key: cacheKey,
        ttl: 15000,
        persist: true,
        fetcher: function() {
          return api.get('/shop/orders', params, { priority: 'critical', silent: true });
        },
        onCache: function(orders) {
          self.setData({ orders });
        },
        onFresh: function(orders) {
          self.setData({ orders });
          if (didLoading) {
            wx.hideLoading();
            didLoading = false;
          }
          resolve();
        },
        onError: function(err) {
          if (didLoading) wx.hideLoading();
          if (cache.get(cacheKey) === undefined) {
            wx.showToast({ title: err.message || '加载失败', icon: 'none' });
          }
          resolve();
        }
      });
      // 命中缓存的话立即解决，不阻塞 UI
      if (cache.get(cacheKey) !== undefined) resolve();
    });
  },

  payOrder: function(e) {
    const orderId = e.currentTarget.dataset.id;
    const self = this;
    wx.showModal({
      title: '提示',
      content: '确认支付该订单？',
      success: function(res) {
        if (res.confirm) {
          api.put('/shop/orders/' + orderId + '/pay', {}, { priority: 'critical' }).then(function() {
            cache.clearPrefix('orders:');
            wx.showToast({ title: '支付成功', icon: 'success' });
            self.loadOrders();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '支付失败', icon: 'none' });
          });
        }
      }
    });
  },

  confirmReceive: function(e) {
    const orderId = e.currentTarget.dataset.id;
    const self = this;
    wx.showModal({
      title: '确认收货',
      content: '确认已收到商品？',
      success: function(res) {
        if (res.confirm) {
          api.put('/shop/orders/' + orderId + '/receive', {}, { priority: 'critical' }).then(function() {
            cache.clearPrefix('orders:');
            wx.showToast({ title: '确认成功', icon: 'success' });
            self.loadOrders();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '操作失败', icon: 'none' });
          });
        }
      }
    });
  },

  viewDetail: function(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/order/detail?id=' + orderId
    });
  },

  onPullDownRefresh: function() {
    cache.clear('orders:' + this.data.currentTab);
    this.loadOrders().then(function() {
      wx.stopPullDownRefresh();
    });
  }
});
