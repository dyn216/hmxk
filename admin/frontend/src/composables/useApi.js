/**
 * useApi
 * 统一封装基于 fetch 的请求方法 + 日期/表单格式化辅助。
 * 业务侧通过 createApi(current) 获得绑定到当前模块（医生/管理）的 request。
 */

const TIMEOUT_MS = 12000;

export function createApi(current) {
  async function request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    const token = localStorage.getItem(current.value.tokenKey);
    if (token) headers.Authorization = `Bearer ${token}`;

    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      const response = await fetch(`${current.value.apiHost}${current.value.prefix}${path}`, {
        ...options,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal
      });
      const contentType = response.headers.get('content-type') || '';
      const payload = contentType.includes('application/json')
        ? await response.json()
        : await response.text();
      if (!response.ok) {
        throw new Error(payload?.detail || payload?.message || '请求失败');
      }
      return payload;
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error('请求超时，请确认后端服务可达');
      }
      throw err;
    } finally {
      window.clearTimeout(timer);
    }
  }

  return { request };
}

export function buildQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) {
      query.set(key, value);
    }
  });
  const text = query.toString();
  return text ? `?${text}` : '';
}

export function compactData(value) {
  return Object.fromEntries(
    Object.entries(value).filter(([, item]) => item !== undefined)
  );
}

export function displayText(value) {
  return value === null || value === undefined || value === '' ? '—' : value;
}

export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function toInputDateTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = item => String(item).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function normalizeFormData(fields, model) {
  const result = {};
  fields.forEach(field => {
    let value = model[field.key];
    if (field.type === 'number') {
      value = value === '' || value === null || value === undefined
        ? undefined
        : Number(value);
    } else if (field.type === 'checkbox') {
      value = Boolean(value);
    } else if (field.emptyAsUndefined && value === '') {
      value = undefined;
    }
    result[field.key] = value;
  });
  return compactData(result);
}
