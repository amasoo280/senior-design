// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Google OAuth Client ID - obtain from Google Cloud Console
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

// API endpoints
export const API_ENDPOINTS = {
  // OAuth endpoints
  googleAuth: `${API_BASE_URL}/auth/google`,
  me: `${API_BASE_URL}/auth/me`,
  logout: `${API_BASE_URL}/auth/logout`,
  verify: `${API_BASE_URL}/auth/verify`,

  // App endpoints
  ask: `${API_BASE_URL}/ask`,
  health: `${API_BASE_URL}/health`,
  dbPing: `${API_BASE_URL}/db-ping`,
  logs: `${API_BASE_URL}/logs`,
  analytics: `${API_BASE_URL}/analytics`,
} as const;

// Default tenant ID (for development)
// Use one of the allowed tenant IDs: c55b3c70-7aa7-11eb-a7e8-9b4baf296adf or eaeddcf1-fb98-11eb-94c9-b1e578657155
export const DEFAULT_TENANT_ID = import.meta.env.VITE_DEFAULT_TENANT_ID;

// Local storage key for auth token
export const AUTH_TOKEN_KEY = 'sargon_auth_token';

// Local storage key for user info
export const USER_INFO_KEY = 'sargon_user_info';
