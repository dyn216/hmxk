Page({
  data: {
    goods: {
      name: '',
      price: 0,
      description: '',
      images: []
    }
  },
  
  onLoad(options) {
    const goodsId = options.id || '1';
    this.loadGoods(goodsId);
  },
  
  loadGoods(id) {
    // 模拟数据
    this.setData({
      goods: {
        name: '智能血压计',
        price: 299,
        description: '家用医疗级血压测量仪，精准测量，智能记录',
        images: ['?']
      }
    });
  },
  
  buyNow() {
    wx.showToast({
      title: '购买功能开发中',
      icon: 'none'
    });
  }
});
