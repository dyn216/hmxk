function formatTime(date) {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return [year, month, day].map(formatNumber).join('/') +
    ' ' + [hour, minute, second].map(formatNumber).join(':')
}

function formatNumber(n) {
  n = n.toString()
  return n[1] ? n : '0' + n
}

// 后端基础地址，开发环境可以是本机 IP:PORT
// 注意：在真机/模拟器上访问本地服务，需要把 127.0.0.1 换成你电脑的局域网 IP
const BASE_URL = 'https://api.yun-an.xyz'

// 通用请求封装
function request(options) {
  options = options || {}
  const url = options.url
  const method = options.method || 'GET'
  const data = options.data || {}
  const header = options.header || {}

  return new Promise(function(resolve, reject) {
    wx.request({
      url: BASE_URL + url,
      method: method,
      data: data,
      header: Object.assign({
        'Content-Type': 'application/json',
      }, header),
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(res)
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

// === 示例 API：登录（患者/医生/管理员共用） ===
function apiLogin(options) {
  options = options || {}
  return request({
    url: '/auth/login',
    method: 'POST',
    data: { phone: options.phone, role: options.role },
  })
}

// === 示例 API：患者上传监测数据（血压/血糖） ===
function apiCreateMeasurement(options) {
  options = options || {}
  return request({
    url: '/patients/' + options.patientId + '/measurements',
    method: 'POST',
    data: {
      type: options.type,
      value1: options.value1,
      value2: options.value2,
      measured_at: options.measuredAt,
    },
  })
}

module.exports = {
  formatTime: formatTime,
  request: request,
  apiLogin: apiLogin,
  apiCreateMeasurement: apiCreateMeasurement,
}
