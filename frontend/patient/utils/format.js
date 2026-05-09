function pad(value) {
  value = Number(value);
  if (isNaN(value)) return '00';
  return value < 10 ? '0' + value : String(value);
}

function parseDate(value) {
  if (!value) return null;
  if (Object.prototype.toString.call(value) === '[object Date]') return value;
  if (typeof value !== 'string' && typeof value !== 'number') return null;
  var normalized = String(value).replace(/-/g, '/').replace('T', ' ');
  var date = new Date(normalized);
  if (isNaN(date.getTime())) return null;
  return date;
}

function formatDateTime(value) {
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(value)) {
    return value.slice(0, 16).replace('T', ' ');
  }
  var date = parseDate(value);
  if (!date) return value || '';
  return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) + ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes());
}

function formatDate(value) {
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) {
    return value.slice(0, 10);
  }
  var date = parseDate(value);
  if (!date) return value || '';
  return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate());
}

function formatTime(value) {
  if (typeof value === 'string' && /^\d{1,2}:\d{2}/.test(value)) {
    return value.slice(0, 5);
  }
  if (typeof value === 'string' && value.indexOf('T') !== -1) {
    return value.split('T')[1].slice(0, 5);
  }
  if (typeof value === 'string' && value.indexOf(' ') !== -1) {
    return value.split(' ')[1].slice(0, 5);
  }
  var date = parseDate(value);
  if (!date) return value || '';
  return pad(date.getHours()) + ':' + pad(date.getMinutes());
}

module.exports = {
  formatDateTime: formatDateTime,
  formatDate: formatDate,
  formatTime: formatTime
};
