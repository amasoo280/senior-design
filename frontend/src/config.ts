// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const DEFAULT_TENANT_ID = import.meta.env.VITE_DEFAULT_TENANT_ID || 'default';

// API endpoints
export const API_ENDPOINTS = {
  ask: `${API_BASE_URL}/ask`,
  health: `${API_BASE_URL}/health`,
} as const;


