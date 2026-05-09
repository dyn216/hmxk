const api = require('../../utils/request.js');
const cache = require('../../utils/cache.js');

Page({
  data: {
    userInfo: {},
    profile: {},
    doctor: null,
    doctorView: null,
    orderCount: 0
  },

  onLoad: function() {
    this.loadAll();
  },

  onShow: function() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 4 });
    }
    this.loadAll();
  },

  // 个人页 + 待支付订单数 并行预拉，先用缓存秒出
  loadAll: function() {
    const self = this;
    cache.swr({
      key: 'profile:detail',
      ttl: 30000,
      persist: true,
      fetcher: function() {
        return api.get('/profile', {}, { priority: 'critical', silent: true });
      },
      onCache: function(profile) {
        self._applyProfile(profile);
      },
      onFresh: function(profile) {
        self._applyProfile(profile);
      },
      onError: function(err) {
        if (cache.get('profile:detail') === undefined) {
          wx.showToast({ title: err.message || '加载失败', icon: 'none' });
        }
      }
    });

    cache.swr({
      key: 'profile:order_count',
      ttl: 15000,
      persist: true,
      fetcher: function() {
        return api.get('/shop/orders', { status: 'pending' }, { priority: 'critical', silent: true }).then(function(list) {
          return (list || []).length;
        });
      },
      onCache: function(count) {
        self.setData({ orderCount: count });
      },
      onFresh: function(count) {
        self.setData({ orderCount: count });
      }
    });
  },

  _applyProfile: function(profile) {
    if (!profile) return;
    const doctor = this._normalizeDoctor(profile.doctor);
    this.setData({
      userInfo: profile.user,
      profile: profile,
      doctor: profile.doctor,
      doctorView: doctor
    });
  },

  _cleanDoctorText: function(value, fallback) {
    value = value === undefined || value === null ? '' : String(value).trim();
    if (!value || value === '1') return fallback;
    return value;
  },

  _normalizeDoctor: function(doctor) {
    if (!doctor) return null;
    const user = doctor.user || {};
    const profile = doctor.profile || {};
    return {
      id: doctor.id || profile.id || doctor.doctor_id,
      name: this._cleanDoctorText(doctor.name || user.name, '签约医生'),
      title: this._cleanDoctorText(doctor.title || profile.title, '医生'),
      department: this._cleanDoctorText(doctor.department || profile.department, '慢病管理')
    };
  },

  editProfile: function() {
    wx.navigateTo({
      url: '/pages/profile/edit'
    });
  },

  goToOrders: function() {
    wx.switchTab({
      url: '/pages/order/list'
    });
  },

  goToPrescriptions: function() {
    wx.switchTab({
      url: '/pages/prescription/list'
    });
  },

  goToMeasurements: function() {
    wx.navigateTo({
      url: '/pages/records/records'
    });
  },

  goToMedications: function() {
    wx.navigateTo({
      url: '/pages/medication/medication'
    });
  },

  viewDoctor: function() {
    if (this.data.doctorView) {
      wx.navigateTo({
        url: '/pages/doctor/doctor?id=' + this.data.doctorView.id
      });
    }
  },

  chatWithDoctor: function() {
    if (this.data.doctorView) {
      wx.navigateTo({
        url: '/pages/consultation/chat?doctorId=' + this.data.doctorView.id
      });
    }
  },

  editAddress: function() {
    wx.navigateTo({
      url: '/pages/profile/address'
    });
  },

  changePassword: function() {
    wx.navigateTo({
      url: '/pages/security/security'
    });
  },

  about: function() {
    wx.navigateTo({
      url: '/pages/about/about'
    });
  },

  logout: function() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      success: function(res) {
        if (res.confirm) {
          wx.removeStorageSync('token');
          wx.removeStorageSync('userInfo');
          // 清空所有用户态缓存，避免下次登录后看到上一个账号的数据
          cache.clearPrefix('');
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      }
    });
  }
});
