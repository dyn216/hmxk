const api = require('../../utils/request.js');

Page({
  data: {
    items: [],
    address: null,
    selectedPrescription: null,
    hasPrescriptionDrug: false,
    remark: '',
    totalPrice: 0,
    shippingFee: 0,
    finalPrice: 0,
    cartIds: [],
    productId: null,
    quantity: 1
  },

  onLoad: function(options) {
    if (options.cartIds) {
      this.setData({
        cartIds: options.cartIds.split(',').map(function(id) { return parseInt(id); })
      });
      this.loadCartItems();
    } else if (options.productId) {
      this.setData({ 
        productId: parseInt(options.productId),
        quantity: parseInt(options.quantity || 1)
      });
      this.loadProductItem();
    }
    
    this.loadDefaultAddress();
  },

  loadCartItems: function() {
    const self = this;
    api.get('/shop/cart', {}, { priority: 'critical' }).then(function(cartList) {
      const items = (cartList || []).filter(function(item) {
        return self.data.cartIds.indexOf(item.id) !== -1;
      });

      const hasPrescription = items.some(function(item) {
        return item.product.is_prescription;
      });

      self.setData({
        items: items,
        hasPrescriptionDrug: hasPrescription
      });
      self.calculatePrice();
    }).catch(function(err) {
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    });
  },

  loadProductItem: function() {
    const self = this;
    api.get('/shop/products/' + this.data.productId, {}, { priority: 'critical' }).then(function(product) {
      const items = [{
        product: product,
        quantity: self.data.quantity
      }];

      self.setData({
        items: items,
        hasPrescriptionDrug: product.is_prescription
      });
      self.calculatePrice();
    }).catch(function(err) {
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    });
  },

  loadDefaultAddress: function() {
    const self = this;
    api.get('/profile', {}, { priority: 'critical', silent: true }).then(function(profile) {
      if (profile.address) {
        self.setData({
          address: {
            name: profile.user.name,
            phone: profile.user.phone,
            address: profile.address
          }
        });
      }
    }).catch(function(err) {
      console.error('加载地址失败:', err);
    });
  },

  calculatePrice: function() {
    const total = this.data.items.reduce(function(sum, item) {
      return sum + (item.product.price * item.quantity);
    }, 0);
    
    const shipping = total >= 99 ? 0 : 10;
    const final = total + shipping;
    
    this.setData({
      totalPrice: total.toFixed(2),
      shippingFee: shipping.toFixed(2),
      finalPrice: final.toFixed(2)
    });
  },

  selectAddress: function() {
    wx.showModal({
      title: '提示',
      content: '请在个人中心完善收货地址',
      showCancel: false
    });
  },

  selectPrescription: function() {
    wx.navigateTo({
      url: '/pages/prescription/select?from=order'
    });
  },

  onRemarkInput: function(e) {
    this.setData({ remark: e.detail.value });
  },

  submitOrder: function() {
    if (!this.data.address) {
      wx.showToast({ title: '请先填写收货地址', icon: 'none' });
      return;
    }

    if (this.data.hasPrescriptionDrug && !this.data.selectedPrescription) {
      wx.showToast({ title: '购买处方药需要选择处方', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '提交中...' });
    
    const self = this;
    try {
      const orderData = {
        items: this.data.items.map(function(item) {
          return {
            product_id: item.product.id,
            quantity: item.quantity,
            price: item.product.price
          };
        }),
        receiver_name: this.data.address.name,
        receiver_phone: this.data.address.phone,
        receiver_address: this.data.address.address,
        remark: this.data.remark
      };

      if (this.data.selectedPrescription) {
        orderData.prescription_id = this.data.selectedPrescription.id;
      }

      api.post('/shop/orders', orderData, { priority: 'critical' }).then(function(order) {
      wx.hideLoading();
      wx.showToast({ 
        title: '下单成功', 
        icon: 'success',
        duration: 1500
      });

      setTimeout(function() {
        wx.redirectTo({
          url: '/pages/order/detail?id=' + order.id
        });
      }, 1500);
      }).catch(function(err) {
        wx.hideLoading();
        wx.showToast({ title: err.message || '提交失败', icon: 'none' });
      });
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '提交失败', icon: 'none' });
    }
  }
});
