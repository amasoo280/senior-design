// API Configuration - use /api proxy in dev to avoid CORS
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '/api' : 'http://localhost:8000');
// Tenant ID must be explicitly set via VITE_DEFAULT_TENANT_ID env var
// Use one of the allowed tenant IDs: c55b3c70-7aa7-11eb-a7e8-9b4baf296adf or eaeddcf1-fb98-11eb-94c9-b1e578657155
export const DEFAULT_TENANT_ID = import.meta.env.VITE_DEFAULT_TENANT_ID;

// API endpoints
export const API_ENDPOINTS = {
  ask: `${API_BASE_URL}/ask`,
  health: `${API_BASE_URL}/health`,
  logs: `${API_BASE_URL}/logs`,
  analytics: `${API_BASE_URL}/analytics`,
  adminConfig: `${API_BASE_URL}/admin/config`,
  login: `${API_BASE_URL}/login`,
  logout: `${API_BASE_URL}/logout`,
  verifyAuth: `${API_BASE_URL}/auth/verify`,
} as const;

// Auth token storage key
export const AUTH_TOKEN_KEY = 'sargon_auth_token';


