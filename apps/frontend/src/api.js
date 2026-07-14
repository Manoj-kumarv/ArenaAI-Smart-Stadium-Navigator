const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
let WS_BASE = import.meta.env.VITE_WS_URL;
if (!WS_BASE) {
  if (BASE.startsWith('https://')) {
    WS_BASE = BASE.replace('https://', 'wss://');
  } else if (BASE.startsWith('http://')) {
    WS_BASE = BASE.replace('http://', 'ws://');
  } else {
    WS_BASE = 'ws://localhost:8000';
  }
}

export const WS_URL = `${WS_BASE}/ws/telemetry`;

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, { method = 'GET', body, token } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(token),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw Object.assign(new Error(err.detail || 'Request failed'), { status: res.status, data: err });
  }
  if (res.status === 204) return null;
  return res.json();
}

// ── Auth ───────────────────────────────────────────────────────────────────────
export const api = {
  login: (username, password) =>
    request('/api/auth/login', { method: 'POST', body: { username, password } }),

  signup: (username, email, password, role) =>
    request('/api/auth/signup', { method: 'POST', body: { username, email, password, role } }),

  me: (token) => request('/api/auth/me', { token }),

  // ── Zones ──────────────────────────────────────────────────────────────────
  getZones: (token) => request('/api/zones', { token }),
  getZone: (id, token) => request(`/api/zones/${id}`, { token }),
  analyseZone: (zoneId, token) =>
    request(`/api/zones/${zoneId}/analyse`, { method: 'POST', token }),
  zoneAction: (payload, token) =>
    request('/api/zones/action', { method: 'POST', body: payload, token }),
  kpi: () => request('/api/zones/kpi/summary'),

  // ── Incidents ──────────────────────────────────────────────────────────────
  getIncidents: (token, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/incidents${qs ? '?' + qs : ''}`, { token });
  },
  createIncident: (body, token) =>
    request('/api/incidents', { method: 'POST', body, token }),
  resolveIncident: (id, token) =>
    request(`/api/incidents/${id}/resolve`, { method: 'POST', token }),

  // ── Broadcast ──────────────────────────────────────────────────────────────
  getBroadcasts: (token) => request('/api/broadcast', { token }),
  createBroadcast: (incident_id, token) =>
    request('/api/broadcast', { method: 'POST', body: { incident_id }, token }),
  getAuditLog: (token, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/broadcast/audit${qs ? '?' + qs : ''}`, { token });
  },

  // ── Fan ────────────────────────────────────────────────────────────────────
  askFan: (query) =>
    request('/api/fan/ask', { method: 'POST', body: { query } }),
};
