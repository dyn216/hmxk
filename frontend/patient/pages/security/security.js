Page({
  data: {
    phoneNumber: '138****0001',
    dataSharing: true,
    deviceCount: 1
  },

  onLoad: function(options) {
    this.loadUserInfo();
  },

  // 加载用户信息
  loadUserInfo: function() {
    // TODO: 从后端获取用户信息
    const userInfo = wx.getStorageSync('userInfo') || {};
    if (userInfo.phone) {
      const phone = userInfo.phone;
      this.setData({
        phoneNumber: phone.substr(0, 3) + '****' + phone.substr(7)
      });
    }
  },

  // 修改密码
  changePassword: function() {
    wx.showModal({
      title: '修改密码',
      content: '请输入旧密码和新密码',
      editable: true,
      placeholderText: '请输入旧密码',
      success: function(res) {
        if (res.confirm) {
          wx.showModal({
            title: '输入新密码',
            content: '请输入6-20位新密码',
            editable: true,
            placeholderText: '请输入新密码',
            success: function(res2) {
              if (res2.confirm) {
                // TODO: 调用后端API修改密码
                wx.showToast({
                  title: '密码修改成功',
                  icon: 'success'
                });
              }
            }
          });
        }
      }
    });
  },

  // 修改手机号
  changePhone: function() {
    const self = this;
    wx.showModal({
      title: '修改手机号',
      content: '请输入新手机号和验证码',
      editable: true,
      placeholderText: '请输入新手机号',
      success: function(res) {
        if (res.confirm) {
          wx.showModal({
            title: '输入验证码',
            content: '验证码已发送至新手机号',
            editable: true,
            placeholderText: '请输入验证码',
            success: function(res2) {
              if (res2.confirm) {
                // TODO: 调用后端API修改手机号
                wx.showToast({
                  title: '手机号修改成功',
                  icon: 'success'
                });
                // 更新显示
                setTimeout(function() {
                  self.loadUserInfo();
                }, 1500);
              }
            }
          });
        }
      }
    });
  },

  // 数据共享开关
  onDataSharingChange: function(e) {
    this.setData({
      dataSharing: e.detail.value
    });
    
    // TODO: 保存设置到后端
    wx.showToast({
      title: e.detail.value ? '已开启数据共享' : '已关闭数据共享',
      icon: 'success',
      duration: 1500
    });
  },

  // 管理登录设备
  manageDevices: function() {
    wx.showModal({
      title: '登录设备',
      content: '当前设备：iPhone 13\n最后登录：2024-01-20 10:30\n\n是否强制退出其他设备？',
      confirmText: '强制退出',
      confirmColor: '#f56c6c',
      success: function(res) {
        if (res.confirm) {
          // TODO: 调用后端API强制退出其他设备
          wx.showToast({
            title: '其他设备已退出',
            icon: 'success'
          });
        }
      }
    });
  },

  // 退出登录
  logout: function() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      confirmColor: '#6a7cfc',
      success: function(res) {
        if (res.confirm) {
          // 清除本地存储
          wx.clearStorageSync();
          
          wx.showToast({
            title: '已退出登录',
            icon: 'success',
            duration: 1500
          });
          
          // 跳转到首页
          setTimeout(function() {
            wx.reLaunch({
              url: '/pages/index/index'
            });
          }, 1500);
        }
      }
    });
  },

  // 注销账号
  deleteAccount: function() {
    wx.showModal({
      title: '注销账号',
      content: '注销后将删除所有数据且无法恢复，确定要注销吗？',
      confirmText: '确定注销',
      confirmColor: '#f56c6c',
      success: function(res) {
        if (res.confirm) {
          wx.showModal({
            title: '再次确认',
            content: '此操作不可逆，请输入"确认注销"继续',
            editable: true,
            placeholderText: '请输入"确认注销"',
            confirmColor: '#f56c6c',
            success: function(res2) {
              if (res2.confirm && res2.content === '确认注销') {
                // TODO: 调用后端API注销账号
                wx.showToast({
                  title: '账号已注销',
                  icon: 'success'
                });
                
                // 清除本地存储并返回首页
                setTimeout(function() {
                  wx.clearStorageSync();
                  wx.reLaunch({
                    url: '/pages/index/index'
                  });
                }, 1500);
              } else {
                wx.showToast({
                  title: '输入错误，已取消',
                  icon: 'none'
                });
              }
            }
          });
        }
      }
    });
  }
});
