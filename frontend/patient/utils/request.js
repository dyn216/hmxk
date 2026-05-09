/**
 * 统一的HTTP请求工具
 */
const config = require('../config.js');
const auth = require('./auth.js');
const network = require('./network.js');
const API_BASE_URL = config.baseURL;

function startsWith(text, prefix) {
  return String(text || '').indexOf(prefix) === 0;
}

function wait(ms) {
  return new Promise(function(resolve) {
    setTimeout(resolve, ms);
  });
}

function normalizeApiPath(url) {
  if (startsWith(url, 'http')) {
    return url
      .replace('http://127.0.0.1:8011', API_BASE_URL)
      .replace('http://127.0.0.1:8012', API_BASE_URL)
      .replace('http://127.0.0.1:8013', API_BASE_URL)
      .replace('http://127.0.0.1:8001', API_BASE_URL)
      .replace('http://192.168.0.100:8001', API_BASE_URL);
  }

  let path = startsWith(url, '/') ? url : '/' + url;
  if (path === config.apiPrefix) {
    path = '/';
  } else if (startsWith(path, config.apiPrefix + '/')) {
    path = path.slice(config.apiPrefix.length);
  }
  if (startsWith(path, '/patient/')) {
    path = path.slice('/patient'.length);
  }
  return API_BASE_URL + config.apiPrefix + path;
}

function getErrorMsg(res) {
  if (res && res.data) {
    return res.data.detail || res.data.message || '请求失败';
  }
  return '请求失败';
}

function showFailToast(message, silent) {
  if (silent) return;
  wx.showToast({
    title: message,
    icon: 'none'
  });
}

/**
 * 发起HTTP请求
 */
function request(options) {
  const defaultOptions = {
    method: 'GET',
    timeout: config.timeout,
    header: {
      'Content-Type': 'application/json'
    }
  };

  const inputOptions = options || {};
  const priority = inputOptions.priority || 'normal';
  const silent = inputOptions.silent === true;
  const policy = network.getRequestPolicy(priority);
  options = Object.assign({}, defaultOptions, inputOptions);
  delete options.priority;
  delete options.silent;
  delete options.retry;

  options.url = normalizeApiPath(options.url);
  options.timeout = inputOptions.timeout || policy.timeout;

  const token = auth.getToken();
  if (token) {
    options.header['Authorization'] = 'Bearer ' + token;
  }

  if (config.enableRequestLog) {
    console.log('🚀 Request:', options.method, options.url, 'API_BASE_URL:', API_BASE_URL);
    if (options.data) {
      console.log('📦 Data:', options.data);
    }
  }

  return runRequest(options, policy.retries, policy.delay, silent);
}

function runRequest(options, retries, delay, silent) {
  return new Promise(function(resolve, reject) {
    const wxOptions = Object.assign({}, options, {
      success: function(res) {
        if (config.enableRequestLog) {
          console.log('✅ Response:', res.statusCode, res.data);
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          handleUnauthorized();
          reject(new Error('未授权，请重新登录'));
        } else if (res.statusCode === 403) {
          showFailToast('没有权限', silent);
          reject(new Error('没有权限'));
        } else if (res.statusCode === 404) {
          showFailToast('请求资源不存在', silent);
          reject(new Error('请求资源不存在'));
        } else if (res.statusCode >= 500) {
          if (retries > 0) {
            wait(delay).then(function() {
              runRequest(options, retries - 1, delay * 2, silent).then(resolve).catch(reject);
            });
          } else {
            showFailToast('服务器错误', silent);
            reject(new Error('服务器错误'));
          }
        } else {
          const errorMsg = getErrorMsg(res);
          showFailToast(errorMsg, silent);
          reject(new Error(errorMsg));
        }
      },
      fail: function(error) {
        console.error('❌ Request failed:', error);
        const errMsg = error && error.errMsg ? error.errMsg : '';
        const isTimeout = errMsg.indexOf('timeout') !== -1;
        const isNetworkFail = errMsg.indexOf('fail') !== -1;

        if (retries > 0 && (isTimeout || isNetworkFail)) {
          network.checkLatency();
          wait(delay).then(function() {
            runRequest(options, retries - 1, delay * 2, silent).then(resolve).catch(reject);
          });
        } else if (isTimeout) {
          showFailToast('请求超时', silent);
          reject(new Error('请求超时'));
        } else if (isNetworkFail) {
          showFailToast('网络连接失败', silent);
          reject(new Error('网络连接失败'));
        } else {
          showFailToast('请求失败', silent);
          reject(error);
        }
      }
    });
    wx.request(wxOptions);
  });
}

/**
 * 处理未授权情况
 */
function handleUnauthorized() {
  auth.clearAuth();
  
  wx.showModal({
    title: '登录已过期',
    content: '请重新登录',
    showCancel: false,
    success: function() {
      wx.reLaunch({
        url: '/pages/login/login'
      });
    }
  });
}

/**
 * GET请求
 */
function get(url, data, options) {
  data = data || {};
  options = options || {};
  return request(Object.assign({}, options, {
    url: url,
    method: 'GET',
    data: data
  }));
}

/**
 * POST请求
 */
function post(url, data, options) {
  data = data || {};
  options = options || {};
  return request(Object.assign({}, options, {
    url: url,
    method: 'POST',
    data: data
  }));
}

/**
 * PUT请求
 */
function put(url, data, options) {
  data = data || {};
  options = options || {};
  return request(Object.assign({}, options, {
    url: url,
    method: 'PUT',
    data: data
  }));
}

/**
 * DELETE请求
 */
function del(url, data, options) {
  data = data || {};
  options = options || {};
  return request(Object.assign({}, options, {
    url: url,
    method: 'DELETE',
    data: data
  }));
}

/**
 * 上传文件
 */
function upload(url, filePath, name, formData) {
  name = name || 'file';
  formData = formData || {};
  const token = auth.getToken();
  let uploadUrl = normalizeApiPath(url);
  if (startsWith(url, '/upload/')) {
    uploadUrl = API_BASE_URL + '/api' + url;
  }
  
  return new Promise(function(resolve, reject) {
    wx.uploadFile({
      url: uploadUrl,
      filePath: filePath,
      name: name,
      formData: formData,
      header: {
        'Authorization': token ? 'Bearer ' + token : ''
      },
      success: function(res) {
        if (res.statusCode === 200) {
          resolve(JSON.parse(res.data));
        } else {
          wx.showToast({
            title: '上传失败',
            icon: 'none'
          });
          reject(new Error('上传失败'));
        }
      },
      fail: function(error) {
        wx.showToast({
          title: '上传失败',
          icon: 'none'
        });
        reject(error);
      }
    });
  });
}

module.exports = {
  request: request,
  get: get,
  post: post,
  put: put,
  delete: del,
  upload: upload
};
