// API client for BHUMI-AI backend
const BASE_URL = 'http://localhost:8000';

function getToken(): string | null {
  return localStorage.getItem('bhumi_token');
}

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request('/auth/me'),

  // Projects
  getProjects: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/projects${q}`);
  },
  getProject: (id: string) => request(`/api/projects/${id}`),
  createProject: (data: any) => request('/api/projects/', { method: 'POST', body: JSON.stringify(data) }),

  // Analytics
  getNationalAnalytics: () => request('/api/analytics/national'),
  getStateAnalytics: (state: string) => request(`/api/analytics/state/${encodeURIComponent(state)}`),

  // Parcels
  getParcels: (projectId?: string) => request(`/api/parcels${projectId ? `?project_id=${projectId}` : ''}`),
  getParcel: (id: string) => request(`/api/parcels/${id}`),

  // AI
  getRisk: (projectId: string) => request(`/api/ai/risk/${projectId}`),
  getAnomalies: () => request('/api/ai/anomalies'),
  copilot: (msg: string, projectId?: string, lang?: string, conversationId?: string, parcelId?: string) =>
    request('/api/ai/copilot', {
      method: 'POST',
      body: JSON.stringify({
        message: msg,
        project_id: projectId,
        language: lang || 'en',
        conversation_id: conversationId,
        parcel_id: parcelId,
      }),
    }),
  simulate: (data: any) => request('/api/ai/simulation', { method: 'POST', body: JSON.stringify(data) }),
  getRecommendations: (projectId: string) => request(`/api/ai/recommendations/${projectId}`),
  analyzeDocument: () => request('/api/ai/document/analyze', { method: 'POST' }),
  executeRecommendation: (data: any) => request('/api/ai/recommendations/execute', { method: 'POST', body: JSON.stringify(data) }),

  // Operations
  getCompensation: (status?: string, projectId?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (projectId) params.append('project_id', projectId);
    const q = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/compensation${q}`);
  },
  updateCompensationStatus: (id: string, status: string) => request(`/api/compensation/${id}/status?new_status=${status}`, { method: 'PUT' }),
  getDisputes: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/disputes${q}`);
  },
  resolveDispute: (id: string, notes: string) =>
    request(`/api/disputes/${id}/resolve?resolution_notes=${encodeURIComponent(notes)}`, { method: 'PUT' }),
  getDocuments: (projectId?: string) => request(`/api/documents${projectId ? `?project_id=${projectId}` : ''}`),
  getTasks: (projectId?: string) => request(`/api/workflow/tasks${projectId ? `?project_id=${projectId}` : ''}`),
  updateTaskStatus: (id: string, status: string) => request(`/api/workflow/tasks/${id}/status?new_status=${status}`, { method: 'PUT' }),
  getNotifications: (unreadOnly?: boolean) => request(`/api/notifications${unreadOnly ? '?unread_only=true' : ''}`),
  markNotifRead: (id: string) => request(`/api/notifications/${id}/read`, { method: 'PUT' }),
  markAllNotifsRead: () => request('/api/notifications/read-all', { method: 'PUT' }),
  getAuditLogs: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/audit${q}`);
  },

  // R&R
  getRR: (parcelId?: string, projectId?: string) => {
    const params = new URLSearchParams();
    if (parcelId) params.append('parcel_id', parcelId);
    if (projectId) params.append('project_id', projectId);
    const q = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/rr${q}`);
  },
  updateRRStatus: (id: string, status: string, notes?: string) =>
    request(`/api/rr/${id}/status?new_status=${status}${notes ? `&notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PUT' }),

  // Field Verification
  submitVerification: (data: any) => request('/api/field/verify', { method: 'POST', body: JSON.stringify(data) }),
  reviewVerification: (id: string, decision: string, notes?: string) =>
    request(`/api/field/verify/${id}/review?decision=${decision}${notes ? `&review_notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PUT' }),

  // Citizen
  trackParcel: (ref: string) => request(`/api/citizen/track/${encodeURIComponent(ref)}`),
};
