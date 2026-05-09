/**
 * 患者端配置文件
 */
module.exports = {
  // API基础配置
  baseURL: 'https://api.yun-an.xyz',
  apiPrefix: '/api/patient',
  timeout: 10000,
  
  // Token配置
  tokenKey: 'patient_token',
  userInfoKey: 'patient_user_info',
  tokenExpireDays: 7,
  
  // 请求日志（生产关闭：低端机上 console.log 会显著拖慢请求耗时）
  enableRequestLog: false,
  
  // 应用信息
  appName: '惠民携康',
  appVersion: '1.0.0'
};
