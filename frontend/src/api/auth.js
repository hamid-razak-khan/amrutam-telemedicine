import apiClient from './axios';

export const register = async (userData) => {
  const response = await apiClient.post('/auth/register', userData);
  return response.data;
};

export const login = async (credentials) => {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
};

export const logout = async (refreshToken) => {
  const response = await apiClient.post('/auth/logout', { refresh: refreshToken });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

export const registerDoctor = async (doctorData) => {
  const response = await apiClient.post('/auth/register-doctor', doctorData);
  return response.data;
};

// Multi-Factor Authentication (MFA) APIs
export const verifyMfaLogin = async ({ mfa_token, code }) => {
  const response = await apiClient.post('/auth/mfa/verify-login', { mfa_token, code });
  return response.data;
};

export const setupMfa = async () => {
  const response = await apiClient.post('/auth/mfa/setup');
  return response.data;
};

export const confirmMfa = async (code) => {
  const response = await apiClient.post('/auth/mfa/confirm', { code });
  return response.data;
};

export const disableMfa = async ({ password, code }) => {
  const response = await apiClient.post('/auth/mfa/disable', { password, code });
  return response.data;
};

export const getMfaStatus = async () => {
  const response = await apiClient.get('/auth/mfa/status');
  return response.data;
};

