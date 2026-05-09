Page({
  data: {
    showDialog: false,
    frequencyOptions: ['每天一次', '每天两次', '每天三次', '隔天一次', '每周两次'],
    frequencyIndex: 0,
    form: {
      name: '',
      time: '08:00',
      dose: '',
      frequency: '每天一次',
      remark: ''
    },
    medications: []
  },
  onLoad() {
    this.loadMedications();
  },
  loadMedications() {
    const medications = this.normalizeMedications(wx.getStorageSync('medications') || []);
    wx.setStorageSync('medications', medications);
    this.setData({ medications });
  },
  normalizeMedications(list) {
    return (list || []).map(function(item) {
      return {
        id: item.id || Date.now(),
        name: String(item.name || item.drug_name || '').trim(),
        time: String(item.time || item.reminder_time || item.reminderTimes || '08:00').slice(0, 5),
        dose: String(item.dose || item.dosage || '').trim(),
        frequency: String(item.frequency || '每天一次').trim(),
        remark: String(item.remark || item.notes || '').trim()
      };
    }).filter(function(item) {
      return item.name;
    });
  },
  showAddDialog() {
    this.setData({
      showDialog: true,
      frequencyIndex: 0,
      form: this.getDefaultForm()
    });
  },
  closeDialog() {
    this.setData({ showDialog: false });
  },
  getDefaultForm() {
    return {
      name: '',
      time: '08:00',
      dose: '',
      frequency: '每天一次',
      remark: ''
    };
  },
  handleNameInput(e) {
    this.setData({ 'form.name': e.detail.value });
  },
  handleTimeChange(e) {
    this.setData({ 'form.time': e.detail.value });
  },
  handleDoseInput(e) {
    this.setData({ 'form.dose': e.detail.value });
  },
  handleFrequencyChange(e) {
    const index = Number(e.detail.value);
    const frequency = this.data.frequencyOptions[index] || '';
    this.setData({
      frequencyIndex: index,
      'form.frequency': frequency
    });
  },
  handleRemarkInput(e) {
    this.setData({ 'form.remark': e.detail.value });
  },
  saveMedication() {
    const form = this.validateForm();
    if (!form) {
      return;
    }
    const medication = {
      id: Date.now(),
      name: form.name,
      time: form.time,
      dose: form.dose,
      frequency: form.frequency,
      remark: form.remark
    };
    const medications = wx.getStorageSync('medications') || [];
    medications.unshift(medication);
    wx.setStorageSync('medications', medications);
    this.setData({
      medications,
      showDialog: false,
      frequencyIndex: 0,
      form: this.getDefaultForm()
    });
    wx.showToast({
      title: '添加成功',
      icon: 'success'
    });
  },
  validateForm() {
    const name = String(this.data.form.name || '').trim();
    const time = String(this.data.form.time || '').trim();
    const dose = String(this.data.form.dose || '').trim();
    const frequency = String(this.data.form.frequency || '').trim();
    const remark = String(this.data.form.remark || '').trim();

    if (!name) {
      wx.showToast({ title: '请输入药品名称', icon: 'none' });
      return null;
    }
    if (name.length > 20) {
      wx.showToast({ title: '药品名称不能超过20个字符', icon: 'none' });
      return null;
    }
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(time)) {
      wx.showToast({ title: '请选择用药时间', icon: 'none' });
      return null;
    }
    if (!dose) {
      wx.showToast({ title: '请输入用药剂量', icon: 'none' });
      return null;
    }
    if (dose.length > 15) {
      wx.showToast({ title: '用药剂量不能超过15个字符', icon: 'none' });
      return null;
    }
    if (!/^\d+(\.\d+)?\s*[\u4e00-\u9fa5a-zA-Zμ]+$/.test(dose)) {
      wx.showToast({ title: '请输入正确的用药剂量', icon: 'none' });
      return null;
    }
    if (!frequency || this.data.frequencyOptions.indexOf(frequency) === -1) {
      wx.showToast({ title: '请选择服用频率', icon: 'none' });
      return null;
    }
    if (remark.length > 50) {
      wx.showToast({ title: '备注不能超过50个字符', icon: 'none' });
      return null;
    }

    return {
      name: name,
      time: time,
      dose: dose,
      frequency: frequency,
      remark: remark
    };
  },
  deleteMedication(e) {
    const id = e.currentTarget.dataset.id;
    const self = this;
    wx.showModal({
      title: '删除确认',
      content: '确定要删除该用药提醒吗？',
      confirmText: '删除',
      confirmColor: '#d93025',
      success(res) {
        if (!res.confirm) return;
        const medications = (wx.getStorageSync('medications') || []).filter(function(item) {
          return String(item.id) !== String(id);
        });
        wx.setStorageSync('medications', medications);
        self.setData({ medications: medications });
        wx.showToast({ title: '删除成功', icon: 'success' });
      }
    });
  }
});