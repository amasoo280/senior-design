/**
 * Auth utilities for Auth0 integration.
 * 
 * Note: Most auth state is managed by Auth0Provider via useAuth0 hook.
 * These utilities provide helper functions for API calls.
 */

import { AUTH_TOKEN_KEY, USER_INFO_KEY, API_ENDPOINTS } from '../config';

/**
 * Get stored auth token (fallback for non-hook contexts).
 * Prefer using useAuth0().getAccessTokenSilently() in components.
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem(AUTH_TOKEN_KEY);
};

export const setAuthToken = (token: string): void => {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
};

export const removeAuthToken = (): void => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(USER_INFO_KEY);
};

export const isAuthenticated = (): boolean => {
  return getAuthToken() !== null;
};

/**
 * Build auth headers using a provided access token.
 * This is the preferred way — pass the token from useAuth0().
 */
export const getAuthHeadersWithToken = (accessToken: string): HeadersInit => {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
  };
};

/**
 * Build auth headers from localStorage fallback.
 */
export const getAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

export const verifyAuth = async (): Promise<boolean> => {
  const token = getAuthToken();
  if (!token) {
    return false;
  }

  try {
    const response = await fetch(API_ENDPOINTS.verify, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    return response.ok;
  } catch {
    return false;
  }
};

export const logout = async (): Promise<void> => {
  const token = getAuthToken();
  if (token) {
    try {
      await fetch(API_ENDPOINTS.logout, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
    } catch {
      // Ignore errors on logout
    }
  }
  removeAuthToken();
};

export const getUserInfo = () => {
  const userInfo = localStorage.getItem(USER_INFO_KEY);
  return userInfo ? JSON.parse(userInfo) : null;
};
