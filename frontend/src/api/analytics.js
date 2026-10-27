import apiClient from './axios';

export const getAnalyticsOverview = async () => {
  const response = await apiClient.get('/admin/analytics/overview');
  return response.data;
};

export const getConsultationTrends = async (days = 14) => {
  const response = await apiClient.get('/admin/analytics/consultations', { params: { days } });
  return response.data;
};
