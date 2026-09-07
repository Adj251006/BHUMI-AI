// API client for BHUMI-AI backend
const BASE_URL = 'http://localhost:8000';

function getToken(): string | null {
  return localStorage.getItem('bhumi_token');
}

function getCitizenToken(): string | null {
  return localStorage.getItem('bhumi_citizen_token');
}

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const isCitizen = path.startsWith('/api/citizen/') && !path.includes('/auth/otp/');
  const token = isCitizen ? (getCitizenToken() || getToken()) : getToken();
  
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
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
    return request(`/api/projects/${q}`);
  },
  getProject: (id: string) => request(`/api/projects/${id}`),
  createProject: (data: any) => request('/api/projects/', { method: 'POST', body: JSON.stringify(data) }),
  getConsentData: (projectId: string) => request(`/api/projects/${projectId}/consent`),

  // Analytics
  getNationalAnalytics: () => request('/api/analytics/national'),
  getStateAnalytics: (state: string) => request(`/api/analytics/state/${encodeURIComponent(state)}`),

  // Parcels
  getParcels: (projectId?: string) => request(`/api/parcels/${projectId ? `?project_id=${projectId}` : ''}`),
  getParcel: (id: string) => request(`/api/parcels/${id}`),

  // AI & Analytics
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
  compareCorridors: (projectId: string) => request(`/api/ai/corridors/${projectId}`),

  // Workflow Statutory Engine
  getWorkflowRules: () => request('/api/workflow/rules'),
  transitionWorkflowStage: (parcelId: string, targetStage: string, remarks?: string) =>
    request('/api/workflow/transition', {
      method: 'POST',
      body: JSON.stringify({ parcel_id: parcelId, target_stage: targetStage, remarks: remarks || '' }),
    }),
  getTasks: (projectId?: string) => request(`/api/workflow/tasks${projectId ? `?project_id=${projectId}` : ''}`),
  updateTaskStatus: (id: string, status: string) => request(`/api/workflow/tasks/${id}/status?new_status=${status}`, { method: 'PUT' }),

  // Compensation & Statutory Calculator
  getCompensation: (status?: string, projectId?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (projectId) params.append('project_id', projectId);
    const q = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/compensation/${q}`);
  },
  updateCompensationStatus: (id: string, status: string) => request(`/api/compensation/${id}/status?new_status=${status}`, { method: 'PUT' }),
  calculateAward: (data: any) => request('/api/compensation/calculate-award', { method: 'POST', body: JSON.stringify(data) }),

  // Disputes
  getDisputes: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/disputes/${q}`);
  },
  resolveDispute: (id: string, notes: string) =>
    request(`/api/disputes/${id}/resolve?resolution_notes=${encodeURIComponent(notes)}`, { method: 'PUT' }),
  fileDispute: (data: any) => request('/api/disputes/', { method: 'POST', body: JSON.stringify(data) }),

  // Documents & AI Compliance
  getDocuments: (projectId?: string) => request(`/api/documents/${projectId ? `?project_id=${projectId}` : ''}`),
  uploadDocument: (formData: FormData) => request('/api/documents/upload', { method: 'POST', body: formData }),

  // Land Bank & Encroachments
  getLandBankSummary: () => request('/api/land-bank/summary'),
  getEncroachments: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/land-bank/encroachments/${q}`);
  },
  reportEncroachment: (data: any) => request('/api/land-bank/encroachments', { method: 'POST', body: JSON.stringify(data) }),
  updateEncroachmentStatus: (id: string, status: string, notes?: string) =>
    request(`/api/land-bank/encroachments/${id}/status?status=${status}${notes ? `&resolution_notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PATCH' }),

  // National Integrations
  getIntegrationsStatus: () => request('/api/integrations/status'),
  triggerIntegrationSync: (systemKey: string) => request(`/api/integrations/sync/${systemKey}`, { method: 'POST' }),

  // Notifications & Outbox
  getNotifications: (unreadOnly?: boolean) => request(`/api/notifications/${unreadOnly ? '?unread_only=true' : ''}`),
  markNotifRead: (id: string) => request(`/api/notifications/${id}/read`, { method: 'PUT' }),
  markAllNotifsRead: () => request('/api/notifications/read-all', { method: 'PUT' }),
  getNotificationsOutbox: () => request('/api/notifications/outbox'),

  // Audit Log & Cryptographic Verification
  getAuditLogs: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/audit/${q}`);
  },
  verifyAuditTrail: () => request('/api/audit/verify'),

  // R&R
  getRR: (parcelId?: string, projectId?: string) => {
    const params = new URLSearchParams();
    if (parcelId) params.append('parcel_id', parcelId);
    if (projectId) params.append('project_id', projectId);
    const q = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/rr/${q}`);
  },
  updateRRStatus: (id: string, status: string, notes?: string) =>
    request(`/api/rr/${id}/status?new_status=${status}${notes ? `&notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PUT' }),

  // Field Verification
  submitVerification: (data: any) => request('/api/field/verify', { method: 'POST', body: JSON.stringify(data) }),
  reviewVerification: (id: string, decision: string, notes?: string) =>
    request(`/api/field/verify/${id}/review?decision=${decision}${notes ? `&review_notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PUT' }),

  // Citizen Portal
  citizenSendOtp: (phone: string) => request('/api/citizen/auth/otp/send', { method: 'POST', body: JSON.stringify({ phone_number: phone }) }),
  citizenVerifyOtp: (phone: string, otp: string) => request('/api/citizen/auth/otp/verify', { method: 'POST', body: JSON.stringify({ phone_number: phone, otp }) }),
  citizenGetParcels: () => request('/api/citizen/parcels'),
  trackParcel: (ref: string) => request(`/api/citizen/track/${encodeURIComponent(ref)}`),
};
