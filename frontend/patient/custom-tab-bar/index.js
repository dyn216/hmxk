const TAB_LIST = [
  { pagePath: '/pages/index/index', text: '首页' },
  { pagePath: '/pages/shop/list', text: '商城' },
  { pagePath: '/pages/order/list', text: '订单' },
  { pagePath: '/pages/prescription/list', text: '处方' },
  { pagePath: '/pages/profile/index', text: '我的' }
];

Component({
  options: {
    // 显式隔离样式：避免页面 wxss 里同名的 .tab-item / .tab-item.active
    // 串到底部 tabbar（例如商城页的分类筛选 tab 把整格刷成蓝色）
    styleIsolation: 'isolated'
  },
  data: {
    selected: 0,
    list: TAB_LIST
  },

  lifetimes: {
    attached() {
      this.updateSelected();
    },
    ready() {
      this.updateSelected();
    }
  },

  pageLifetimes: {
    show() {
      this.updateSelected();
    }
  },

  methods: {
    updateSelected() {
      const pages = getCurrentPages();
      const current = pages[pages.length - 1];
      if (!current) return;
      const route = '/' + current.route;
      let selected = -1;
      for (let i = 0; i < TAB_LIST.length; i++) {
        if (TAB_LIST[i].pagePath === route) {
          selected = i;
          break;
        }
      }
      if (selected !== -1 && selected !== this.data.selected) {
        this.setData({ selected });
      }
    },

    switchTab(e) {
      if (this._switching) return;
      const dataset = e.currentTarget.dataset || {};
      const index = Number(dataset.index);
      const target = TAB_LIST[index];
      if (!target) return;
      const path = target.pagePath;
      const pages = getCurrentPages();
      const current = pages[pages.length - 1];
      if (current && '/' + current.route === path) {
        this.updateSelected();
        return;
      }

      this._switching = true;
      const self = this;
      const timer = setTimeout(function() {
        self._switching = false;
        self.updateSelected();
      }, 1200);

      wx.switchTab({
        url: path,
        success: function() {
          self.setData({ selected: index });
        },
        fail: function() {
          // 切换失败时回退高亮，避免与实际页面状态不一致
          self.updateSelected();
        },
        complete: function() {
          clearTimeout(timer);
          setTimeout(function() {
            self._switching = false;
            self.updateSelected();
          }, 300);
        }
      });
    }
  }
});
