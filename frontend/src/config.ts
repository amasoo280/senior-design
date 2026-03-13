// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Auth0 Configuration
export const AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN || '';
export const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID || '';
export const AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE || `${API_BASE_URL}`;

// API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  me: `${API_BASE_URL}/auth/me`,
  logout: `${API_BASE_URL}/auth/logout`,
  verify: `${API_BASE_URL}/auth/verify`,

  // App endpoints
  ask: `${API_BASE_URL}/ask`,
  askStream: `${API_BASE_URL}/ask/stream`,
  health: `${API_BASE_URL}/health`,
  dbPing: `${API_BASE_URL}/db-ping`,
  logs: `${API_BASE_URL}/logs`,
  analytics: `${API_BASE_URL}/analytics`,

  // Admin (require admin role)
  adminConfigGuardrails: `${API_BASE_URL}/admin/config/guardrails`,
  adminConfigPrompt: `${API_BASE_URL}/admin/config/prompt`,
  adminConfigLlm: `${API_BASE_URL}/admin/config/llm`,
  adminMetrics: `${API_BASE_URL}/admin/metrics`,
  adminMetricsAccounts: `${API_BASE_URL}/admin/metrics/accounts`,
  adminMetricsAccount: (tenantId: string) => `${API_BASE_URL}/admin/metrics/account/${encodeURIComponent(tenantId)}`,
  adminLogs: `${API_BASE_URL}/admin/logs`,
} as const;

// Default tenant ID (for development)
// Use one of the allowed tenant IDs: c55b3c70-7aa7-11eb-a7e8-9b4baf296adf or eaeddcf1-fb98-11eb-94c9-b1e578657155
export const DEFAULT_TENANT_ID = import.meta.env.VITE_DEFAULT_TENANT_ID;

// Local storage key for auth token
export const AUTH_TOKEN_KEY = 'sargon_auth_token';

// Local storage key for user info
export const USER_INFO_KEY = 'sargon_user_info';
