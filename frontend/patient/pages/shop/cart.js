const api = require('../../utils/request.js');

Page({
  data: {
    cartItems: [],
    allChecked: false,
    checkedCount: 0,
    totalPrice: 0
  },

  onLoad: function() {
    this.loadCart();
  },

  onShow: function() {
    this.loadCart();
  },

  loadCart: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    return api.get('/shop/cart', {}, { priority: 'critical' }).then(function(res) {
      const items = (res || []).map(function(item) {
        return Object.assign({}, item, { checked: false });
      });
      self.setData({ cartItems: items });
      self.calculateTotal();
      wx.hideLoading();
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    });
  },

  onItemCheck: function(e) {
    const id = parseInt(e.currentTarget.dataset.id);
    const items = this.data.cartItems.map(function(item) {
      if (item.id === id) {
        return Object.assign({}, item, { checked: !item.checked });
      }
      return item;
    });
    
    this.setData({ cartItems: items });
    this.calculateTotal();
  },

  onSelectAll: function(e) {
    const checked = (e.detail.value || []).indexOf('all') !== -1;
    const items = this.data.cartItems.map(function(item) {
      return Object.assign({}, item, { checked: checked });
    });
    
    this.setData({ 
      cartItems: items,
      allChecked: checked
    });
    this.calculateTotal();
  },

  calculateTotal: function() {
    const checkedItems = this.data.cartItems.filter(function(item) { return item.checked; });
    const total = checkedItems.reduce(function(sum, item) {
      return sum + (item.product.price * item.quantity);
    }, 0);
    
    this.setData({
      checkedCount: checkedItems.length,
      totalPrice: total.toFixed(2),
      allChecked: checkedItems.length === this.data.cartItems.length && this.data.cartItems.length > 0
    });
  },

  increaseQuantity: function(e) {
    const id = e.currentTarget.dataset.id;
    const item = this.findCartItem(id);
    if (!item) return;

    const self = this;
    api.put('/shop/cart/' + id, {
        quantity: item.quantity + 1
      }, { priority: 'critical' }).then(function() {
      self.loadCart();
    }).catch(function(err) {
      wx.showToast({ title: err.message || '操作失败', icon: 'none' });
    });
  },

  decreaseQuantity: function(e) {
    const id = e.currentTarget.dataset.id;
    const item = this.findCartItem(id);
    if (!item) return;
    
    if (item.quantity <= 1) {
      wx.showToast({ title: '数量不能小于1', icon: 'none' });
      return;
    }
    
    const self = this;
    api.put('/shop/cart/' + id, {
        quantity: item.quantity - 1
      }, { priority: 'critical' }).then(function() {
      self.loadCart();
    }).catch(function(err) {
      wx.showToast({ title: err.message || '操作失败', icon: 'none' });
    });
  },

  removeItem: function(e) {
    const id = e.currentTarget.dataset.id;
    const self = this;
    wx.showModal({
      title: '确认删除',
      content: '确定要从购物车中移除该商品吗？',
      success: function(res) {
        if (res.confirm) {
          api.delete('/shop/cart/' + id, {}, { priority: 'critical' }).then(function() {
            wx.showToast({ title: '已移除', icon: 'success' });
            self.loadCart();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '删除失败', icon: 'none' });
          });
        }
      }
    });
  },

  checkout: function() {
    const checkedItems = this.data.cartItems.filter(function(item) { return item.checked; });
    
    if (checkedItems.length === 0) {
      wx.showToast({ title: '请选择要结算的商品', icon: 'none' });
      return;
    }

    // 检查是否有处方药
    const hasPrescriptionDrug = checkedItems.some(function(item) { return item.product.is_prescription; });
    
    if (hasPrescriptionDrug) {
      wx.showModal({
        title: '处方药提示',
        content: '购物车中包含处方药，需要提供医生开具的处方',
        confirmText: '选择处方',
        success: function(res) {
          if (res.confirm) {
            // 跳转到处方选择页面
            wx.navigateTo({ 
              url: '/pages/prescription/select?from=cart'
            });
          }
        }
      });
      return;
    }

    // 跳转到订单确认页面
    const itemIds = checkedItems.map(function(item) { return item.id; }).join(',');
    wx.navigateTo({ 
      url: '/pages/order/confirm?cartIds=' + itemIds
    });
  },

  goToShop: function() {
    wx.switchTab({ url: '/pages/shop/list' });
  },

  findCartItem: function(id) {
    id = parseInt(id);
    for (let i = 0; i < this.data.cartItems.length; i++) {
      if (this.data.cartItems[i].id === id) return this.data.cartItems[i];
    }
    return null;
  },

  onPullDownRefresh: function() {
    this.loadCart().then(function() {
      wx.stopPullDownRefresh();
    });
  }
});
