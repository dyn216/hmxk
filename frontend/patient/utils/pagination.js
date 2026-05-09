/**
 * 分页加载工具类
 * 提供统一的分页、上拉加载、下拉刷新功能
 */

function PaginationHelper(options) {
  options = options || {};
  this.page = 1;                          // 当前页码
  this.pageSize = options.pageSize || 20; // 每页数量
  this.total = 0;                         // 总记录数
  this.totalPages = 0;                    // 总页数
  this.hasNext = false;                   // 是否有下一页
  this.hasPrev = false;                   // 是否有上一页
  this.loading = false;                   // 是否正在加载
  this.finished = false;                  // 是否加载完成
  this.list = [];                         // 数据列表
}

  /**
   * 重置分页状态
   */
PaginationHelper.prototype.reset = function() {
  this.page = 1;
  this.total = 0;
  this.totalPages = 0;
  this.hasNext = false;
  this.hasPrev = false;
  this.loading = false;
  this.finished = false;
  this.list = [];
};

  /**
   * 加载第一页（下拉刷新）
   */
PaginationHelper.prototype.loadFirstPage = function(loadFunc) {
  this.reset();
  return this.loadPage(loadFunc);
};

  /**
   * 加载下一页（上拉加载更多）
   */
PaginationHelper.prototype.loadNextPage = function(loadFunc) {
  if (this.loading || this.finished) {
    return Promise.resolve();
  }

  this.page++;
  return this.loadPage(loadFunc);
};

  /**
   * 加载指定页
   */
PaginationHelper.prototype.loadPage = function(loadFunc) {
  const self = this;
  if (self.loading) {
    return Promise.resolve();
  }

  self.loading = true;

  return Promise.resolve(loadFunc(self.page, self.pageSize))
    .then(function(result) {
      result = result || {};

      // 更新分页信息
      self.total = result.total || 0;
      self.totalPages = result.total_pages || 0;
      self.hasNext = result.has_next || false;
      self.hasPrev = result.has_prev || false;

      // 更新数据列表
      if (self.page === 1) {
        self.list = result.items || [];
      } else {
        self.list = self.list.concat(result.items || []);
      }

      // 判断是否加载完成
      self.finished = !self.hasNext;
      self.loading = false;

      return result;
    })
    .catch(function(error) {
      self.loading = false;
      console.error('分页加载失败:', error);
      throw error;
    });
};

  /**
   * 获取当前状态
   */
PaginationHelper.prototype.getState = function() {
  return {
    page: this.page,
    pageSize: this.pageSize,
    total: this.total,
    totalPages: this.totalPages,
    hasNext: this.hasNext,
    hasPrev: this.hasPrev,
    loading: this.loading,
    finished: this.finished,
    list: this.list
  };
};

/**
 * 为页面添加分页功能的Mixin
 */
const PaginationMixin = {
  data: function() {
    return {
      pagination: {
        page: 1,
        pageSize: 20,
        total: 0,
        totalPages: 0,
        hasNext: false,
        loading: false,
        finished: false
      },
      list: []
    };
  },

  methods: {
    /**
     * 初始化分页
     */
    initPagination: function(pageSize) {
      pageSize = pageSize || 20;
      this.pagination = {
        page: 1,
        pageSize: pageSize,
        total: 0,
        totalPages: 0,
        hasNext: false,
        loading: false,
        finished: false
      };
      this.list = [];
    },

    /**
     * 下拉刷新
     */
    onPullDownRefresh: function(loadFunc) {
      this.initPagination(this.pagination.pageSize);

      return this.loadPageData(loadFunc).then(function() {
        wx.showToast({
          title: '刷新成功',
          icon: 'success'
        });
      }).catch(function() {
        wx.showToast({
          title: '刷新失败',
          icon: 'none'
        });
      }).then(function() {
        wx.stopPullDownRefresh();
      });
    },

    /**
     * 上拉加载更多
     */
    onReachBottom: function(loadFunc) {
      if (this.pagination.loading || this.pagination.finished) {
        return;
      }

      this.pagination.page++;
      return this.loadPageData(loadFunc);
    },

    /**
     * 加载分页数据
     */
    loadPageData: function(loadFunc) {
      const self = this;
      if (self.pagination.loading) {
        return Promise.resolve();
      }

      self.pagination.loading = true;

      return Promise.resolve(loadFunc(self.pagination.page, self.pagination.pageSize))
        .then(function(result) {
          result = result || {};

          // 更新分页信息
          self.pagination.total = result.total || 0;
          self.pagination.totalPages = result.total_pages || 0;
          self.pagination.hasNext = result.has_next || false;

          // 更新数据列表
          if (self.pagination.page === 1) {
            self.list = result.items || [];
          } else {
            self.list = self.list.concat(result.items || []);
          }

          // 判断是否加载完成
          self.pagination.finished = !self.pagination.hasNext;
          self.pagination.loading = false;

          return result;
        })
        .catch(function(error) {
          self.pagination.loading = false;
          console.error('加载数据失败:', error);
          throw error;
        });
    }
  }
};

module.exports = {
  PaginationHelper,
  PaginationMixin
};
