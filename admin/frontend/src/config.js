const apiHost = 'https://api.yun-an.xyz';

export const modules = {
  doctor: {
    title: '医生工作台',
    roleName: '医生端',
    apiHost,
    prefix: '/api/doctor',
    tokenKey: 'web_doctor_token',
    userKey: 'web_doctor_user',
    nav: [
      { key: 'dashboard', label: '工作概览' },
      { key: 'patients', label: '患者管理' },
      { key: 'consultations', label: '问诊管理' },
      { key: 'prescriptions', label: '处方管理' },
      { key: 'profile', label: '个人资料' }
    ]
  },
  admin: {
    title: '管理后台',
    roleName: '管理端',
    apiHost,
    prefix: '/api/admin',
    tokenKey: 'web_admin_token',
    userKey: 'web_admin_user',
    nav: [
      { key: 'dashboard', label: '平台概览' },
      { key: 'users', label: '用户管理' },
      { key: 'products', label: '药品管理' },
      { key: 'orders', label: '订单管理' },
      { key: 'prescriptions', label: '处方审核' },
      { key: 'doctors', label: '医生档案' },
      { key: 'patients', label: '患者档案' }
    ]
  }
};
