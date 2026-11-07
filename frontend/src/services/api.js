const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

const request = async (url, options = {}) => {
  const token = localStorage.getItem('trustshield_token');
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  } catch {
    throw new Error('Cannot reach the TrustShield server. Check your internet connection and confirm the backend API URL is configured.');
  }
  const data = await res.json().catch(() => ({ detail: 'Unexpected server response' }));
  if (!res.ok) {
    if (res.status === 401 && url !== '/api/auth/login') { localStorage.removeItem('trustshield_token'); window.dispatchEvent(new Event('trustshield:unauthorized')); }
    throw new Error(data.detail || data.message || `Request failed (${res.status})`);
  }
  return data;
};

export const auth = {
  login: (body) => request('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  register: (body) => request('/api/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  me: () => request('/api/auth/me'),
  forgotPassword: (body) => request('/api/auth/forgot-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  resetPassword: (body) => request('/api/auth/reset-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
};

export const analysis = {
  upload: (file, type) => { const fd = new FormData(); fd.append('file', file); fd.append('document_type', type); return request('/api/analyze', { method: 'POST', body: fd }); },
  history: () => request('/api/history'),
  get: (id) => request(`/api/analysis/${id}`),
  remove: (id) => request(`/api/analysis/${id}`, { method: 'DELETE' }),
  downloadReport: async (id) => {
    const token = localStorage.getItem('trustshield_token');
    const res = await fetch(`${API_BASE}/api/analysis/${id}/report`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Could not download the report. Please sign in again.');
    }
    return res.blob();
  },
};
