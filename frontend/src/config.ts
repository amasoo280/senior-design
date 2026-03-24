// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Auth0 Configuration
export const AUTH0_DOMAIN = import.meta.env.VITE_AUTH0_DOMAIN || '';
export const AUTH0_CLIENT_ID = import.meta.env.VITE_AUTH0_CLIENT_ID || '';
/** Only set via VITE_AUTH0_AUDIENCE — must match an API Identifier in Auth0 (APIs). If unset, no audience is sent (avoids "Service not found"). */
export const AUTH0_AUDIENCE = (import.meta.env.VITE_AUTH0_AUDIENCE || '').trim();

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

/**
 * "Show SQL" in chat: off in production builds by default.
 * - If VITE_SHOW_SQL is unset: true only when running `vite` (npm run dev), false for `vite build` / deployed sites.
 * - VITE_SHOW_SQL=true / false overrides that (e.g. force off while running dev, or on for a staging preview).
 */
function parseShowSqlUi(): boolean {
  const raw = import.meta.env.VITE_SHOW_SQL;
  if (raw === undefined || raw === '') {
    return import.meta.env.DEV;
  }
  return raw === 'true' || raw === '1';
}

export const SHOW_SQL_UI = parseShowSqlUi();

// Local storage key for auth token
export const AUTH_TOKEN_KEY = 'sargon_auth_token';

// Local storage key for user info
export const USER_INFO_KEY = 'sargon_user_info';
