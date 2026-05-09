const RECORDS_KEY = 'bloodPressureRecords';
const api = require('../../utils/request.js');

Page({
  data: {
    record: null,
    tipsContent: ''
  },

  onLoad: function (options) {
    const id = options.id;
    const records = wx.getStorageSync(RECORDS_KEY) || [];
    const record = this.findRecord(records, id);
    
    if (!record) {
      wx.showToast({
        title: '记录不存在',
        icon: 'none'
      });
      setTimeout(function() {
        wx.navigateBack();
      }, 1500);
      return;
    }
    
    this.setData({
      record: record
    });
    this.generateTips();
  },

  // 生成健康建议
  generateTips: function() {
    const record = this.data.record;
    if (!record) {
      return;
    }
    
    const status = record.status;
    let tipsContent = '';
    if (status === 'high') {
      tipsContent = '1. 减少盐的摄入，控制每日不超过5克\n2. 增加有氧运动，每周3-5次，每次30分钟\n3. 保持健康体重，BMI控制在18.5-24之间\n4. 戒烟限酒，控制饮酒量\n5. 定期监测血压，建议每日早晚各一次';
    } else if (status === 'elevated') {
      tipsContent = '1. 血压稍高，建议连续多次测量观察\n2. 清淡饮食，减少油脂和盐分摄入\n3. 保持规律作息，避免熬夜和情绪波动\n4. 适当增加步行等中等强度运动\n5. 如持续偏高，建议咨询医生';
    } else if (status === 'low') {
      tipsContent = '1. 适当增加盐分摄入，维持电解质平衡\n2. 避免突然起身，防止头晕\n3. 保持充足水分摄入\n4. 均衡饮食，保证足够营养\n5. 定期监测血压，如症状加重请及时就医';
    } else {
      tipsContent = '1. 保持健康的生活方式，均衡饮食\n2. 坚持规律运动，每周至少150分钟中等强度运动\n3. 控制体重，保持BMI在18.5-24之间\n4. 戒烟限酒，保持良好的作息习惯\n5. 定期监测血压，维持健康状态';
    }
    this.setData({
      tipsContent: tipsContent
    });
  },

  findRecord: function(records, id) {
    id = parseInt(id);
    for (let i = 0; i < records.length; i++) {
      if (records[i].id === id) return records[i];
    }
    return null;
  },

  // 删除记录（添加了自动刷新）
  deleteRecord: function () {
    const id = this.data.record.id;
    const self = this;
    api.delete('/measurements/' + id, {}, { priority: 'critical' }).then(function() {
      self.removeLocalRecord(id);
    }).catch(function(err) {
      wx.showToast({
        title: err.message || '删除失败',
        icon: 'none'
      });
    });
  },

  removeLocalRecord: function(id) {
    const records = wx.getStorageSync(RECORDS_KEY) || [];
    const newRecords = records.filter(function(item) { return item.id !== id; });
    
    // 更新本地存储
    wx.setStorageSync(RECORDS_KEY, newRecords);
    
    // 显示删除成功提示
    wx.showToast({
      title: '记录删除成功',
      icon: 'success',
      duration: 2000
    });
    
    // 返回记录列表页
    wx.navigateBack({
      delta: 1
    });
  }
});