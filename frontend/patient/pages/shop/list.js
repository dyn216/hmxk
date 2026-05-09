const api = require('../../utils/request.js');
const cache = require('../../utils/cache.js');
const pagination = require('../../utils/pagination.js');
const PaginationHelper = pagination.PaginationHelper;

Page({
  data: {
    products: [],
    activeCategory: '',
    cartCount: 0,
    pagination: {
      loading: false,
      finished: false,
      page: 1,
      pageSize: 20
    }
  },

  paginationHelper: null,
  cartCountLoading: false,

  onLoad: function() {
    this.paginationHelper = new PaginationHelper({ pageSize: 20 });
    // 上次进商城时缓存的首屏商品，立即贴上来再后台拉新
    const cachedFirstPage = cache.get('shop:products:first');
    if (Array.isArray(cachedFirstPage) && cachedFirstPage.length) {
      this.setData({ products: cachedFirstPage });
    }
    this.loadProducts();
  },

  onShow: function() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
    this.loadCartCount();
  },

  loadProducts: function(isRefresh) {
    const self = this;
    const loadTask = isRefresh
      ? this.paginationHelper.loadFirstPage(this.fetchProducts.bind(this))
      : this.paginationHelper.loadPage(this.fetchProducts.bind(this));

    return Promise.resolve(loadTask).then(function() {
      const state = self.paginationHelper.getState();
      self.setData({
        products: state.list,
        pagination: {
          loading: state.loading,
          finished: state.finished,
          page: state.page,
          pageSize: state.pageSize
        }
      });

      // 默认分类下首屏商品列表持久化，下次进入秒出
      if (!self.data.activeCategory && state.page <= 2) {
        cache.write('shop:products:first', state.list.slice(0, 20), true);
      }
    });
  },

  fetchProducts: function(page, pageSize) {
    const params = {
      page: page,
      page_size: pageSize,
      status: true
    };
    
    if (this.data.activeCategory) {
      params.category = this.data.activeCategory;
    }

    return api.get('/shop/products', params, { priority: 'critical', silent: true });
  },

  loadCartCount: function() {
    if (this.cartCountLoading) return;
    const self = this;
    this.cartCountLoading = true;
    cache.swr({
      key: 'shop:cart_count',
      ttl: 10000,
      persist: true,
      fetcher: function() {
        return api.get('/shop/cart', {}, { priority: 'critical', silent: true }).then(function(res) {
          return (res || []).reduce(function(sum, item) {
            return sum + item.quantity;
          }, 0);
        });
      },
      onCache: function(count) {
        self.setData({ cartCount: count });
      },
      onFresh: function(count) {
        self.setData({ cartCount: count });
        self.cartCountLoading = false;
      },
      onError: function() {
        self.cartCountLoading = false;
      }
    });
    // 命中缓存即时释放锁
    if (cache.get('shop:cart_count') !== undefined) {
      this.cartCountLoading = false;
    }
  },

  switchCategory: function(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({ activeCategory: category });
    this.paginationHelper.reset();
    this.loadProducts(true);
  },

  viewDetail: function(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/shop/detail?id=' + id });
  },

  addToCart: function(e) {
    const id = e.currentTarget.dataset.id;
    const prescription = e.currentTarget.dataset.prescription;
    const self = this;
    
    if (prescription) {
      wx.showModal({
        title: '处方药提示',
        content: '该药品为处方药，需要医生开具处方后才能购买',
        showCancel: false
      });
      return;
    }

    api.post('/shop/cart', {
        product_id: id,
        quantity: 1
      }, { priority: 'critical' }).then(function() {
      cache.clear('shop:cart_count');
      wx.showToast({ title: '已加入购物车', icon: 'success' });
      self.loadCartCount();
    }).catch(function(err) {
      wx.showToast({ title: err.message || '添加失败', icon: 'none' });
    });
  },

  goToCart: function() {
    wx.navigateTo({ url: '/pages/shop/cart' });
  },

  onPullDownRefresh: function() {
    const self = this;
    cache.clear('shop:cart_count');
    cache.clear('shop:products:first');
    return this.loadProducts(true).then(function() {
      self.loadCartCount();
      wx.showToast({ title: '刷新成功', icon: 'success' });
    }).catch(function() {
      wx.showToast({ title: '刷新失败', icon: 'none' });
    }).then(function() {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom: function() {
    if (this.data.pagination.loading || this.data.pagination.finished) {
      return;
    }

    const self = this;
    return this.paginationHelper.loadNextPage(this.fetchProducts.bind(this)).then(function() {
      const state = self.paginationHelper.getState();
      self.setData({
        products: state.list,
        pagination: {
          loading: state.loading,
          finished: state.finished,
          page: state.page,
          pageSize: state.pageSize
        }
      });
    });
  }
});
