import { API_ENDPOINTS, AUTH_TOKEN_KEY, USER_INFO_KEY } from '../config';

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
