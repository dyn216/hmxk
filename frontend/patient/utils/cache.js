/**
 * 轻量级前端缓存
 * - 内存层：进程级 Map，热路径零开销
 * - 持久层：可选 wx.storage，冷启动 / 切回前台时回填
 * - SWR 模式：先把缓存渲染上屏，后台静默 revalidate
 *
 * 用法：
 *   const cache = require('../../utils/cache.js');
 *   cache.swr({
 *     key: 'orders:all',
 *     ttl: 15_000,
 *     fetcher: () => api.get('/shop/orders'),
 *     onCache: data => this.setData({ orders: data }),
 *     onFresh: data => this.setData({ orders: data }),
 *     persist: true
 *   });
 */

const PREFIX = 'cache:';
const memory = {};

function hasOwn(obj, key) {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

function startsWith(text, prefix) {
  return String(text || '').indexOf(prefix) === 0;
}

function read(key) {
  if (hasOwn(memory, key)) return memory[key];
  try {
    const raw = wx.getStorageSync(PREFIX + key);
    if (raw && typeof raw === 'object' && typeof raw.t === 'number') {
      memory[key] = raw;
      return raw;
    }
  } catch (_) {}
  return null;
}

function get(key) {
  const entry = read(key);
  return entry ? entry.v : undefined;
}

function isFresh(key, ttlMs) {
  const entry = read(key);
  return Boolean(entry) && (Date.now() - entry.t) < ttlMs;
}

function write(key, value, persist) {
  const entry = { v: value, t: Date.now() };
  memory[key] = entry;
  if (persist) {
    try {
      wx.setStorage({ key: PREFIX + key, data: entry });
    } catch (_) {}
  }
}

function clear(key) {
  delete memory[key];
  try {
    wx.removeStorageSync(PREFIX + key);
  } catch (_) {}
}

function clearPrefix(keyPrefix) {
  keyPrefix = keyPrefix || '';
  Object.keys(memory).forEach(function(key) {
    if (startsWith(key, keyPrefix)) delete memory[key];
  });
  try {
    const info = wx.getStorageInfoSync();
    (info.keys || []).forEach(function(k) {
      if (startsWith(k, PREFIX + keyPrefix)) {
        try { wx.removeStorageSync(k); } catch (_) {}
      }
    });
  } catch (_) {}
}

/**
 * Stale-While-Revalidate
 * - 命中缓存：onCache 同步触发，立刻把上次数据贴到 UI
 * - 没缓存或 TTL 过期：后台 fetcher() → onFresh
 * - fetcher 失败时不会清缓存，避免误把弱网时的失败覆盖掉旧数据
 */
function swr(options) {
  options = options || {};
  const key = options.key;
  const ttl = options.ttl || 0;
  const fetcher = options.fetcher;
  const onCache = options.onCache;
  const onFresh = options.onFresh;
  const onError = options.onError;
  const persist = options.persist;
  const cached = get(key);
  if (cached !== undefined && typeof onCache === 'function') {
    try { onCache(cached); } catch (e) { console.error('cache onCache failed', e); }
  }

  if (typeof fetcher !== 'function') return cached;

  if (cached === undefined || !isFresh(key, ttl)) {
    Promise.resolve()
      .then(function() { return fetcher(); })
      .then(function(data) {
        if (data === undefined) return;
        write(key, data, persist);
        if (typeof onFresh === 'function') onFresh(data);
      })
      .catch(function(err) {
        if (typeof onError === 'function') onError(err);
      });
  }
  return cached;
}

module.exports = { get, read, write, clear, clearPrefix, isFresh, swr };
