import apiClient from './axios';

export const getAuditLogs = async (params = {}) => {
  const response = await apiClient.get('/admin/audit-logs', { params });
  return response.data;
};
