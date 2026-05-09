const shopAPI = require('../../api/shop.js');

Page({
  data: {
    categories: [
      { id: "hypertension", name: "高血压用药", iconClass: "hypertension" },
      { id: "diabetes", name: "糖尿病用药", iconClass: "diabetes" },
      { id: "cardiovascular", name: "心血管用药", iconClass: "cardio" },
      { id: "common", name: "常用药品", iconClass: "common" },
      { id: "health", name: "保健品", iconClass: "health" }
    ],
    currentCategory: "hypertension",
    loading: false,
    goodsData: [],
    currentGoods: []
  },

  onLoad: function() {
    this.loadProducts();
  },

  loadProducts: function(category) {
    const self = this;
    this.setData({ loading: true });

    const params = {};
    if (category) {
      params.category = category;
    }

    return shopAPI.getProducts(params).then(function(products) {
      const goodsData = (products || []).map(function(product) {
        return {
          id: product.id,
          categoryId: product.category,
          name: product.name + '（' + (product.specification || '') + '）',
          desc: product.description || '',
          price: product.price,
          formattedPrice: product.price.toFixed(2),
          imageIcon: '药',
          stock: product.stock,
          is_prescription: product.is_prescription
        };
      });

      self.setData({
        goodsData: goodsData,
        loading: false 
      });

      if (category) {
        self.filterGoodsByCategory(category);
      } else {
        self.filterGoodsByCategory(self.data.currentCategory);
      }
    }).catch(function(error) {
      console.error('加载商品失败:', error);
      self.setData({ loading: false });
      wx.showToast({
        title: '加载商品失败',
        icon: 'none'
      });
    });
  },

  switchCategory: function(e) {
    const categoryId = e.currentTarget.dataset.id;
    this.setData({
      currentCategory: categoryId
    });
    this.loadProducts(categoryId);
  },

  filterGoodsByCategory: function(categoryId) {
    const currentGoods = this.data.goodsData.filter(function(item) {
      return item.categoryId === categoryId;
    }).map(function(item) {
      return Object.assign({}, item, {
        formattedPrice: Number(item.price).toFixed(2)
      });
    });
    this.setData({ currentGoods: currentGoods });
  },

  addToCart: function(e) {
    const goodsId = e.currentTarget.dataset.id;
    const goods = this.findGoods(goodsId);
    if (!goods) return;
    
    if (goods.stock <= 0) {
      wx.showToast({
        title: '商品已售罄',
        icon: 'none'
      });
      return;
    }
    
    if (goods.is_prescription) {
      const self = this;
      wx.showModal({
        title: '处方药提示',
        content: '此商品为处方药，需要医生处方才能购买。是否继续加入购物车？',
        confirmText: '继续',
        cancelText: '取消',
        success: function(result) {
          if (result.confirm) {
            self.doAddToCart(goods, goodsId);
          }
        }
      });
      return;
    }

    this.doAddToCart(goods, goodsId);
  },

  doAddToCart: function(goods, goodsId) {
    shopAPI.addToCart({
        product_id: goodsId,
        quantity: 1
      }).then(function() {
      wx.showToast({
        title: goods.name.split('（')[0] + '已加入购物车',
        icon: "success",
        duration: 1500
      });
    }).catch(function(error) {
      console.error('加入购物车失败:', error);
      wx.showToast({
        title: '加入购物车失败',
        icon: 'none'
      });
    });
  },

  findGoods: function(goodsId) {
    for (let i = 0; i < this.data.goodsData.length; i++) {
      if (this.data.goodsData[i].id === goodsId) return this.data.goodsData[i];
    }
    return null;
  },

  goToGoodsDetail: function(e) {
    const goodsId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/goods-detail/goods-detail?id=' + goodsId
    });
  }
});
