/**
 * 认证工具 - JWT Token管理
 */
const config = require('../config.js');

/**
 * 保存Token
 */
function setToken(token) {
  try {
    wx.setStorageSync(config.tokenKey, token);
    const expireTime = Date.now() + config.tokenExpireDays * 24 * 60 * 60 * 1000;
    wx.setStorageSync(config.tokenKey + '_expire', expireTime);
    return true;
  } catch (error) {
    console.error('保存Token失败:', error);
    return false;
  }
}

/**
 * 获取Token
 */
function getToken() {
  try {
    const token = wx.getStorageSync(config.tokenKey);
    if (!token) {
      return null;
    }

    const expireTime = wx.getStorageSync(config.tokenKey + '_expire');
    if (expireTime && Date.now() > expireTime) {
      clearAuth();
      return null;
    }

    return token;
  } catch (error) {
    console.error('获取Token失败:', error);
    return null;
  }
}

/**
 * 移除Token
 */
function removeToken() {
  try {
    wx.removeStorageSync(config.tokenKey);
    wx.removeStorageSync(config.tokenKey + '_expire');
    return true;
  } catch (error) {
    console.error('移除Token失败:', error);
    return false;
  }
}

/**
 * 保存用户信息
 */
function setUserInfo(userInfo) {
  try {
    wx.setStorageSync(config.userInfoKey, userInfo);
    return true;
  } catch (error) {
    console.error('保存用户信息失败:', error);
    return false;
  }
}

/**
 * 获取用户信息
 */
function getUserInfo() {
  try {
    return wx.getStorageSync(config.userInfoKey) || null;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    return null;
  }
}

/**
 * 移除用户信息
 */
function removeUserInfo() {
  try {
    wx.removeStorageSync(config.userInfoKey);
    return true;
  } catch (error) {
    console.error('移除用户信息失败:', error);
    return false;
  }
}

/**
 * 检查是否已登录
 */
function isLoggedIn() {
  return !!getToken();
}

/**
 * 清除所有认证信息
 */
function clearAuth() {
  removeToken();
  removeUserInfo();
}

/**
 * 登录
 */
function login(phone, password) {
  const request = require('./request.js');
  
  return request.post('/login', {
    phone: phone,
    password: password
  }).then(function(data) {
    if (data.token) {
      setToken(data.token);
      
      const userInfo = {
        user_id: data.user_id,
        role: data.role,
        name: data.name,
        avatar: data.avatar
      };
      setUserInfo(userInfo);
      
      return data;
    } else {
      throw new Error('登录失败：未返回Token');
    }
  });
}

/**
 * 退出登录
 */
function logout() {
  clearAuth();
  
  wx.reLaunch({
    url: '/pages/login/login'
  });
}

module.exports = {
  setToken: setToken,
  getToken: getToken,
  removeToken: removeToken,
  setUserInfo: setUserInfo,
  getUserInfo: getUserInfo,
  removeUserInfo: removeUserInfo,
  isLoggedIn: isLoggedIn,
  clearAuth: clearAuth,
  login: login,
  logout: logout
};
