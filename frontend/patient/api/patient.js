/**
 * 患者端API接口
 */
const request = require('../utils/request.js');

/**
 * 登录
 */
function login(phone, password) {
  return request.post('/login', { phone, password });
}

/**
 * 获取个人档案
 */
function getProfile(options) {
  return request.get('/profile', {}, options);
}

/**
 * 更新个人档案
 */
function updateProfile(data) {
  return request.put('/profile', data);
}

/**
 * 获取监测数据列表
 */
function getMeasurements(params, options) {
  params = params || {};
  return request.get('/measurements', params, options);
}

function normalizeMeasurement(data) {
  const normalized = Object.assign({}, data);
  if (!normalized.type && normalized.measurement_type) {
    normalized.type = normalized.measurement_type;
  }
  if (normalized.value1 === undefined) {
    if (normalized.systolic !== undefined) {
      normalized.value1 = normalized.systolic;
    } else if (normalized.blood_sugar !== undefined) {
      normalized.value1 = normalized.blood_sugar;
    } else if (normalized.heart_rate !== undefined) {
      normalized.value1 = normalized.heart_rate;
    }
  }
  if (normalized.value2 === undefined && normalized.diastolic !== undefined) {
    normalized.value2 = normalized.diastolic;
  }
  if (!normalized.measured_at) {
    normalized.measured_at = new Date().toISOString();
  }
  delete normalized.measurement_type;
  delete normalized.systolic;
  delete normalized.diastolic;
  delete normalized.heart_rate;
  delete normalized.blood_sugar;
  return normalized;
}

/**
 * 创建监测数据
 */
function createMeasurement(data) {
  return request.post('/measurements', normalizeMeasurement(data));
}

/**
 * 获取监测数据统计
 */
function getMeasurementStats(params) {
  params = params || {};
  return request.get('/measurements/stats', params);
}

/**
 * 获取用药列表
 */
function getMedications(options) {
  return request.get('/medications', {}, options);
}

/**
 * 添加用药记录
 */
function createMedication(data) {
  return request.post('/medications', data);
}

/**
 * 更新用药记录
 */
function updateMedication(id, data) {
  return request.put('/medications/' + id, data);
}

/**
 * 删除用药记录
 */
function deleteMedication(id) {
  return request.delete('/medications/' + id);
}

/**
 * 获取监护人列表
 */
function getGuardians() {
  return request.get('/guardians');
}

/**
 * 添加监护人
 */
function createGuardian(data) {
  return request.post('/guardians', data);
}

/**
 * 删除监护人
 */
function deleteGuardian(id) {
  return request.delete('/guardians/' + id);
}

/**
 * 获取设备列表
 */
function getDevices() {
  return request.get('/devices');
}

/**
 * 获取医生列表
 */
function getDoctors(params, options) {
  params = params || {};
  return request.get('/doctors', params, options);
}

/**
 * 获取问诊记录
 */
function getConsultations(params) {
  params = params || {};
  return request.get('/consultations', params);
}

/**
 * 创建问诊记录
 */
function createConsultation(data) {
  return request.post('/consultations', data);
}

/**
 * 获取消息列表
 */
function getMessages(params) {
  params = params || {};
  return request.get('/messages', params);
}

/**
 * 发送消息
 */
function sendMessage(data) {
  return request.post('/messages', data);
}

/**
 * 获取健康报告
 */
function getHealthReport(params) {
  params = params || {};
  return request.get('/health-report', params);
}

/**
 * AI 健康助手：获取对话历史
 */
function getAiChatHistory(options) {
  options = options || {};
  return request.get('/ai/chat/history', {}, options);
}

/**
 * AI 健康助手：发送一条消息
 */
function sendAiChat(content, options) {
  options = Object.assign({ timeout: 60000 }, options || {});
  return request.post('/ai/chat', { content: content }, options);
}

/**
 * AI 健康助手：清空对话
 */
function clearAiChat() {
  return request.delete('/ai/chat');
}

/**
 * AI 测量建议
 */
function getAiMeasurementAdvice(payload, options) {
  options = Object.assign({ timeout: 60000 }, options || {});
  return request.post('/ai/measurement-advice', payload || {}, options);
}

module.exports = {
  login,
  getProfile,
  updateProfile,
  getMeasurements,
  createMeasurement,
  getMeasurementStats,
  getMedications,
  createMedication,
  updateMedication,
  deleteMedication,
  getGuardians,
  createGuardian,
  deleteGuardian,
  getDevices,
  getDoctors,
  getConsultations,
  createConsultation,
  getMessages,
  sendMessage,
  getHealthReport,
  getAiChatHistory,
  sendAiChat,
  clearAiChat,
  getAiMeasurementAdvice
};
