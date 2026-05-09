const api = require('../../utils/request.js');

Page({
  data: {
    addresses: [],
    showModal: false,
    editingId: null,
    addressForm: {
      name: '',
      phone: '',
      address: '',
      is_default: false
    }
  },

  onLoad: function() {
    this.loadAddresses();
  },

  onShow: function() {
    this.loadAddresses();
  },

  loadAddresses: function() {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    return api.get('/addresses', {}, { priority: 'critical' }).then(function(addresses) {
      self.setData({ addresses: addresses });
      wx.hideLoading();
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    });
  },

  addAddress: function() {
    this.setData({
      showModal: true,
      editingId: null,
      addressForm: {
        name: '',
        phone: '',
        address: '',
        is_default: false
      }
    });
  },

  editAddress: function(e) {
    const id = e.currentTarget.dataset.id;
    const address = this.findAddress(id);
    
    if (address) {
      this.setData({
        showModal: true,
        editingId: id,
        addressForm: {
          name: address.name,
          phone: address.phone,
          address: address.address,
          is_default: address.is_default
        }
      });
    }
  },

  setDefault: function(e) {
    const id = e.currentTarget.dataset.id;
    const self = this;
    api.put('/addresses/' + id + '/default', {}, { priority: 'critical' }).then(function() {
      wx.showToast({ title: '设置成功', icon: 'success' });
      self.loadAddresses();
    }).catch(function(err) {
      wx.showToast({ title: err.message || '操作失败', icon: 'none' });
    });
  },

  deleteAddress: function(e) {
    const id = e.currentTarget.dataset.id;
    const self = this;
    wx.showModal({
      title: '删除地址',
      content: '确定要删除该地址吗？',
      success: function(res) {
        if (res.confirm) {
          api.delete('/addresses/' + id, {}, { priority: 'critical' }).then(function() {
            wx.showToast({ title: '删除成功', icon: 'success' });
            self.loadAddresses();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '删除失败', icon: 'none' });
          });
        }
      }
    });
  },

  onFormInput: function(e) {
    const field = e.currentTarget.dataset.field;
    const data = {};
    data['addressForm.' + field] = e.detail.value;
    this.setData(data);
  },

  toggleDefault: function() {
    this.setData({
      'addressForm.is_default': !this.data.addressForm.is_default
    });
  },

  saveAddress: function() {
    const name = this.data.addressForm.name;
    const phone = this.data.addressForm.phone;
    const address = this.data.addressForm.address;
    
    if (!name || !phone || !address) {
      wx.showToast({ title: '请填写完整信息', icon: 'none' });
      return;
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '手机号格式不正确', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '保存中...' });
    const task = this.data.editingId
      ? api.put('/addresses/' + this.data.editingId, this.data.addressForm, { priority: 'critical' })
      : api.post('/addresses', this.data.addressForm, { priority: 'critical' });

    const self = this;
    task.then(function() {
      wx.showToast({ title: '保存成功', icon: 'success' });
      self.closeModal();
      self.loadAddresses();
      wx.hideLoading();
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '保存失败', icon: 'none' });
    });
  },

  findAddress: function(id) {
    id = parseInt(id);
    for (let i = 0; i < this.data.addresses.length; i++) {
      if (this.data.addresses[i].id === id) return this.data.addresses[i];
    }
    return null;
  },

  closeModal: function() {
    this.setData({ showModal: false });
  },

  stopPropagation: function() {
    // 阻止事件冒泡
  }
});
