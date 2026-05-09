/**
 * 商城API服务
 */
const request = require('../utils/request.js');

const shopAPI = {
  /**
   * 获取商品列表
   */
  getProducts: function(params) {
    params = params || {};
    return request.get('/shop/products', params);
  },

  /**
   * 获取商品详情
   */
  getProductDetail: function(productId) {
    return request.get('/shop/products/' + productId);
  },

  /**
   * 添加到购物车
   */
  addToCart: function(data) {
    return request.post('/shop/cart', data);
  },

  /**
   * 获取购物车列表
   */
  getCart: function() {
    return request.get('/shop/cart');
  },

  /**
   * 更新购物车商品数量
   */
  updateCartItem: function(cartId, quantity) {
    return request.put('/shop/cart/' + cartId, { quantity: quantity });
  },

  /**
   * 从购物车删除商品
   */
  removeFromCart: function(cartId) {
    return request.delete('/shop/cart/' + cartId);
  },

  /**
   * 清空购物车
   */
  clearCart: function() {
    return request.delete('/shop/cart');
  },

  /**
   * 创建订单
   */
  createOrder: function(data) {
    return request.post('/shop/orders', data);
  },

  /**
   * 获取订单列表
   */
  getOrders: function(params) {
    params = params || {};
    return request.get('/shop/orders', params);
  },

  /**
   * 获取订单详情
   */
  getOrderDetail: function(orderId) {
    return request.get('/shop/orders/' + orderId);
  },

  /**
   * 取消订单
   */
  cancelOrder: function(orderId) {
    return request.delete('/shop/orders/' + orderId);
  }
};

module.exports = shopAPI;
