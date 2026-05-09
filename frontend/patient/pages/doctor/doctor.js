var api = require('../../utils/request.js');

Page({
  data: {
    doctors: [],
    allDoctors: [],
    departments: [],
    selectedDoctorId: null,
    selectedDoctor: null,
    searchKey: '',
    currentDept: 'all',
    loading: false,
    errorText: ''
  },

  onLoad: function(options) {
    var id = options && options.id ? parseInt(options.id, 10) : null;
    this.setData({
      selectedDoctorId: isNaN(id) ? null : id
    });
    this.loadDoctors();
  },

  onShow: function() {
    if (this.data.allDoctors.length) {
      this.loadDoctors(true);
    }
  },

  loadDoctors: function(silent) {
    var self = this;
    silent = silent === true;
    if (!silent) {
      this.setData({ loading: true, errorText: '' });
      wx.showLoading({ title: '加载医生...' });
    }
    return api.get('/doctors', {}, { priority: 'critical', silent: silent }).then(function(list) {
      var doctors = self.normalizeDoctors(list || []);
      self.applyDoctorData(doctors);
      if (!silent) {
        wx.hideLoading();
      }
    }).catch(function(err) {
      if (!silent) {
        wx.hideLoading();
      }
      self.setData({
        loading: false,
        errorText: err.message || '医生数据加载失败'
      });
      wx.showToast({
        title: err.message || '医生数据加载失败',
        icon: 'none'
      });
    });
  },

  applyDoctorData: function(doctors) {
    var selectedDoctor = null;
    var selectedId = this.data.selectedDoctorId;
    var departments = [];
    var deptMap = {};
    var i;
    for (i = 0; i < doctors.length; i++) {
      if (selectedId && doctors[i].id === selectedId) {
        selectedDoctor = doctors[i];
      }
      if (doctors[i].department && !deptMap[doctors[i].department]) {
        deptMap[doctors[i].department] = true;
        departments.push(doctors[i].department);
      }
    }
    this.setData({
      allDoctors: doctors,
      departments: departments,
      selectedDoctor: selectedDoctor,
      loading: false,
      errorText: ''
    });
    this.filterDoctors();
    if (selectedId && !selectedDoctor) {
      this.loadSelectedDoctor(selectedId);
    }
  },

  loadSelectedDoctor: function(id) {
    var self = this;
    api.get('/doctor/profile?doctor_id=' + encodeURIComponent(id), {}, { priority: 'critical', silent: true }).then(function(doctor) {
      doctor = self.normalizeDoctor(doctor);
      if (!doctor.id) return;
      var allDoctors = self.data.allDoctors.slice();
      var exists = false;
      var i;
      for (i = 0; i < allDoctors.length; i++) {
        if (allDoctors[i].id === doctor.id) {
          allDoctors[i] = doctor;
          exists = true;
        }
      }
      if (!exists) {
        allDoctors.unshift(doctor);
      }
      self.setData({
        allDoctors: allDoctors,
        selectedDoctor: doctor
      });
      self.filterDoctors();
    }).catch(function() {});
  },

  normalizeDoctors: function(list) {
    var result = [];
    var i;
    for (i = 0; i < list.length; i++) {
      result.push(this.normalizeDoctor(list[i]));
    }
    return result;
  },

  normalizeDoctor: function(doctor) {
    doctor = doctor || {};
    var user = doctor.user || {};
    var profile = doctor.profile || {};
    var id = doctor.id || profile.id || doctor.doctor_id;
    var parsedId = parseInt(id, 10);
    if (!isNaN(parsedId)) {
      id = parsedId;
    }
    var name = doctor.name || user.name || '医生';
    var title = this.cleanText(doctor.title || profile.title, '');
    var department = this.cleanText(doctor.department || profile.department, '');
    var hospital = this.cleanText(doctor.hospital || profile.hospital, '');
    var specialty = this.cleanText(doctor.specialty || doctor.introduction || profile.introduction, '');
    var metaParts = [];
    if (title) metaParts.push(title);
    if (department) metaParts.push(department);
    if (hospital) metaParts.push(hospital);
    return {
      id: id,
      user_id: doctor.user_id || user.id || profile.user_id,
      name: this.cleanText(name, '医生'),
      title: title,
      department: department,
      hospital: hospital,
      specialty: specialty,
      metaText: metaParts.join(' · '),
      introduction: this.cleanText(doctor.introduction || profile.introduction, ''),
      avatar: doctor.avatar || user.avatar || '',
      patient_count: doctor.patient_count || 0,
      consultation_count: doctor.consultation_count || 0,
      online: doctor.online !== false,
      can_video: doctor.can_video !== false
    };
  },

  cleanText: function(value, fallback) {
    value = value === undefined || value === null ? '' : String(value).trim();
    if (!value || value === '1') return fallback;
    return value;
  },

  filterDoctors: function() {
    var filtered = this.data.allDoctors.slice();
    var selectedId = this.data.selectedDoctorId;
    var dept = this.data.currentDept;
    var key = (this.data.searchKey || '').toLowerCase();
    if (dept !== 'all') {
      filtered = filtered.filter(function(doctor) {
        return doctor.department === dept;
      });
    }
    if (key) {
      filtered = filtered.filter(function(doctor) {
        return doctor.name.toLowerCase().indexOf(key) !== -1 ||
          doctor.department.toLowerCase().indexOf(key) !== -1 ||
          doctor.specialty.toLowerCase().indexOf(key) !== -1 ||
          doctor.title.toLowerCase().indexOf(key) !== -1;
      });
    }
    if (selectedId) {
      filtered.sort(function(a, b) {
        if (a.id === selectedId) return -1;
        if (b.id === selectedId) return 1;
        return 0;
      });
    }
    this.setData({ doctors: filtered });
  },

  onSearchInput: function(e) {
    this.setData({ searchKey: e.detail.value || '' });
    this.filterDoctors();
  },

  switchDepartment: function(e) {
    this.setData({ currentDept: e.currentTarget.dataset.dept || 'all' });
    this.filterDoctors();
  },

  selectDoctor: function(e) {
    var doctor = this.findDoctor(e.currentTarget.dataset.id);
    if (!doctor) return;
    this.setData({
      selectedDoctorId: doctor.id,
      selectedDoctor: doctor
    });
    this.filterDoctors();
  },

  findDoctor: function(id) {
    id = parseInt(id, 10);
    if (isNaN(id)) return null;
    var doctors = this.data.allDoctors;
    var i;
    for (i = 0; i < doctors.length; i++) {
      if (doctors[i].id === id) return doctors[i];
    }
    return null;
  },

  // 文字咨询
  chatWithDoctor: function(e) {
    var doctor = this.findDoctor(e.currentTarget.dataset.id);
    if (!doctor) {
      wx.showToast({ title: '医生信息错误', icon: 'none' });
      return;
    }
    if (!doctor.online) {
      wx.showToast({
        title: '医生当前不可咨询',
        icon: 'none'
      });
      return;
    }
    wx.navigateTo({
      url: '/pages/consultation/chat?doctorId=' + encodeURIComponent(doctor.id)
    });
  },

  // 开始视频通话
  startVideoCall: function(e) {
    var doctor = this.findDoctor(e.currentTarget.dataset.id);
    if (!doctor) {
      wx.showToast({ title: '医生信息错误', icon: 'none' });
      return;
    }
    if (!doctor.online || !doctor.can_video) {
      wx.showToast({
        title: '医生当前不可视频',
        icon: 'none'
      });
      return;
    }
    wx.navigateTo({
      url: '/pages/video-call/video-call?doctorId=' + encodeURIComponent(doctor.id) + '&doctorName=' + encodeURIComponent(doctor.name) + '&department=' + encodeURIComponent(doctor.department)
    });
  },

  onPullDownRefresh: function() {
    this.loadDoctors(true).then(function() {
      wx.stopPullDownRefresh();
    }).catch(function() {
      wx.stopPullDownRefresh();
    });
  }
});