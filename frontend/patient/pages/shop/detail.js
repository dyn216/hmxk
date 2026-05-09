const api = require('../../utils/request.js');

Page({
  data: {
    productId: null,
    product: {},
    categoryName: '',
    navTop: 20,
    navHeight: 44
  },

  onLoad: function(options) {
    this.initNavBar();
    if (options.id) {
      this.setData({ productId: options.id });
      this.loadProductDetail();
    }
  },

  initNavBar: function() {
    var systemInfo = wx.getSystemInfoSync();
    var statusBarHeight = systemInfo.statusBarHeight || 20;
    var navHeight = 44;
    if (wx.getMenuButtonBoundingClientRect) {
      var menuButton = wx.getMenuButtonBoundingClientRect();
      navHeight = (menuButton.top - statusBarHeight) * 2 + menuButton.height;
    }
    this.setData({
      navTop: statusBarHeight,
      navHeight: navHeight
    });
  },

  goBack: function() {
    var pages = getCurrentPages();
    if (pages.length > 1) {
      wx.navigateBack();
      return;
    }
    wx.switchTab({
      url: '/pages/shop/list'
    });
  },

  loadProductDetail: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    api.get('/shop/products/' + this.data.productId, {}, { priority: 'critical' }).then(function(product) {
      const categoryMap = {
        'hypertension': '高血压用药',
        'diabetes': '糖尿病用药',
        'hyperlipidemia': '高血脂用药',
        'cardiovascular': '心血管用药',
        'other': '其他'
      };
      
      self.setData({
        product: product,
        categoryName: categoryMap[product.category] || '其他'
      });
      wx.hideLoading();
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
      setTimeout(function() {
        wx.navigateBack();
      }, 1500);
    });
  },

  addToCart: function() {
    if (!this.data.product.id) return;

    if (this.data.product.is_prescription) {
      wx.showModal({
        title: '处方药提示',
        content: '该药品为处方药，需要医生开具处方后才能购买',
        showCancel: false
      });
      return;
    }

    api.post('/shop/cart', {
        product_id: this.data.product.id,
        quantity: 1
      }, { priority: 'critical' }).then(function() {
      wx.showToast({ 
        title: '已加入购物车', 
        icon: 'success',
        duration: 1500
      });
    }).catch(function(err) {
      wx.showToast({ title: err.message || '添加失败', icon: 'none' });
    });
  },

  buyNow: function() {
    if (!this.data.product.id) return;

    if (this.data.product.is_prescription) {
      wx.showModal({
        title: '处方药提示',
        content: '该药品为处方药，需要医生开具处方后才能购买',
        showCancel: false
      });
      return;
    }

    wx.navigateTo({
      url: '/pages/order/confirm?productId=' + this.data.product.id + '&quantity=1'
    });
  }
});
