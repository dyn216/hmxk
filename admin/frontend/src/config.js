const localHosts = ['localhost', '127.0.0.1', '0.0.0.0'];
const isLanHost = /^10\./.test(window.location.hostname)
  || /^192\.168\./.test(window.location.hostname)
  || /^172\.(1[6-9]|2\d|3[0-1])\./.test(window.location.hostname);
const defaultApiHost = (localHosts.includes(window.location.hostname) || isLanHost)
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : 'https://api.yun-an.xyz';
const apiHost = import.meta.env.VITE_API_HOST || defaultApiHost;

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
      { key: 'situation', label: '态势感知' },
      { key: 'users', label: '用户管理' },
      { key: 'products', label: '药品管理' },
      { key: 'orders', label: '订单管理' },
      { key: 'prescriptions', label: '处方审核' },
      { key: 'doctors', label: '医生档案' },
      { key: 'patients', label: '患者档案' }
    ]
  }
};
