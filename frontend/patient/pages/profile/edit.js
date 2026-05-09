const api = require('../../utils/request.js');

Page({
  data: {
    formData: {
      name: '',
      gender: '',
      age: '',
      phone: '',
      chronic_diseases: '',
      allergies: '',
      address: '',
      avatar: ''
    },
    genders: ['男', '女'],
    genderIndex: 0
  },

  onLoad: function() {
    this.loadProfile();
  },

  loadProfile: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    api.get('/profile', {}, { priority: 'critical' }).then(function(profile) {
      const genderIndex = this.data.genders.indexOf(profile.gender);

      self.setData({
        formData: {
          name: profile.user.name || '',
          gender: profile.gender || '',
          age: profile.age || '',
          phone: profile.user.phone || '',
          chronic_diseases: profile.chronic_diseases || '',
          allergies: profile.allergies || '',
          address: profile.address || '',
          avatar: profile.user.avatar || ''
        },
        genderIndex: genderIndex >= 0 ? genderIndex : 0
      });
      wx.hideLoading();
    }.bind(this)).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    });
  },

  onInputChange: function(e) {
    const field = e.currentTarget.dataset.field;
    const data = {};
    data['formData.' + field] = e.detail.value;
    this.setData(data);
  },

  onGenderChange: function(e) {
    const index = e.detail.value;
    this.setData({
      genderIndex: index,
      'formData.gender': this.data.genders[index]
    });
  },

  uploadAvatar: function() {
    const self = this;
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: function(res) {
        const tempFilePath = res.tempFilePaths[0];
        
        wx.showLoading({ title: '上传中...' });
        api.upload('/upload/image', tempFilePath).then(function(uploadRes) {
          self.setData({
            'formData.avatar': uploadRes.url
          });
          wx.hideLoading();
          wx.showToast({ title: '上传成功', icon: 'success' });
        }).catch(function() {
          wx.hideLoading();
          wx.showToast({ title: '上传失败', icon: 'none' });
        });
      }
    });
  },

  submit: function() {
    const name = this.data.formData.name;
    const gender = this.data.formData.gender;
    const age = this.data.formData.age;
    
    if (!name || !gender || !age) {
      wx.showToast({ title: '请填写必填项', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '保存中...' });
    const data = Object.assign({}, this.data.formData, {
      age: parseInt(age)
    });

    api.put('/profile', data, { priority: 'critical' }).then(function() {
      wx.hideLoading();
      wx.showToast({ 
        title: '保存成功', 
        icon: 'success',
        duration: 1500
      });

      setTimeout(function() {
        wx.navigateBack();
      }, 1500);
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '保存失败', icon: 'none' });
    });
  },

  cancel: function() {
    wx.navigateBack();
  }
});
