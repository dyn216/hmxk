const config = require('../config.js');

const state = {
  networkType: 'unknown',
  isConnected: true,
  level: 'good',
  latency: 0,
  updatedAt: 0
};

let inited = false;
let checking = false;
const listeners = [];

function copyState() {
  return {
    networkType: state.networkType,
    isConnected: state.isConnected,
    level: state.level,
    latency: state.latency,
    updatedAt: state.updatedAt
  };
}

function contains(list, value) {
  return list.indexOf(value) !== -1;
}

function classify(networkType, isConnected) {
  if (isConnected === false || networkType === 'none') return 'weak';
  if (contains(['2g', '3g', 'unknown'], networkType)) return networkType === '3g' ? 'medium' : 'weak';
  return 'good';
}

function emit() {
  const snapshot = copyState();
  listeners.slice().forEach(function(listener) {
    try { listener(snapshot); } catch (_) {}
  });
}

function update(next) {
  next = next || {};
  let changed = false;
  Object.keys(next).forEach(function(key) {
    if (state[key] !== next[key]) {
      state[key] = next[key];
      changed = true;
    }
  });
  state.updatedAt = Date.now();
  if (changed) emit();
}

function init() {
  if (inited) return;
  inited = true;

  wx.getNetworkType({
    success: function(res) {
      const networkType = res.networkType || 'unknown';
      update({
        networkType: networkType,
        isConnected: networkType !== 'none',
        level: classify(networkType, networkType !== 'none')
      });
    }
  });

  if (wx.onNetworkStatusChange) {
    wx.onNetworkStatusChange(function(res) {
      const networkType = res.networkType || 'unknown';
      update({
        networkType: networkType,
        isConnected: res.isConnected,
        level: classify(networkType, res.isConnected)
      });
      checkLatency();
    });
  }

  checkLatency();
}

function checkLatency() {
  if (checking) return Promise.resolve(state.level);
  checking = true;
  const startedAt = Date.now();

  return new Promise(function(resolve) {
    wx.request({
      url: config.baseURL + '/health?t=' + startedAt,
      method: 'GET',
      timeout: 3000,
      success: function() {
        const latency = Date.now() - startedAt;
        const level = latency > 1000 ? 'weak' : (latency > 500 ? 'medium' : 'good');
        update({
          latency: latency,
          level: level,
          isConnected: true
        });
        resolve(level);
      },
      fail: function() {
        update({
          latency: 3000,
          level: 'weak'
        });
        resolve('weak');
      },
      complete: function() {
        checking = false;
      }
    });
  });
}

function getState() {
  return copyState();
}

function isWeak() {
  return state.level === 'weak' || state.isConnected === false || state.networkType === 'none' || state.networkType === '2g';
}

function getRequestPolicy(priority) {
  const weak = isWeak();
  const critical = priority === 'critical';
  return {
    timeout: weak ? 15000 : config.timeout,
    retries: weak ? (critical ? 2 : 1) : 1,
    delay: weak ? 800 : 400
  };
}

function onChange(listener) {
  if (typeof listener !== 'function') return function() {};
  listeners.push(listener);
  return function() {
    const index = listeners.indexOf(listener);
    if (index !== -1) listeners.splice(index, 1);
  };
}

module.exports = {
  init: init,
  checkLatency: checkLatency,
  getState: getState,
  isWeak: isWeak,
  getRequestPolicy: getRequestPolicy,
  onChange: onChange
};
