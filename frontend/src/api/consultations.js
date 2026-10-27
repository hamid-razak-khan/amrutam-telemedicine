import apiClient from './axios';

export const getConsultations = async () => {
  const response = await apiClient.get('/consultations');
  return response.data;
};

export const getConsultationDetail = async (id) => {
  const response = await apiClient.get(`/consultations/${id}`);
  return response.data;
};

export const startConsultation = async (id, notes = '') => {
  const response = await apiClient.post(`/consultations/${id}/start`, { notes });
  return response.data;
};

export const completeConsultation = async (id, clinicalNotes = '') => {
  const response = await apiClient.post(`/consultations/${id}/complete`, { clinical_notes: clinicalNotes });
  return response.data;
};
