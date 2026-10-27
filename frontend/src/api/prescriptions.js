import apiClient from './axios';

export const createPrescription = async (consultationId, prescriptionData) => {
  const response = await apiClient.post(`/consultations/${consultationId}/prescriptions`, prescriptionData);
  return response.data;
};

export const getPrescriptions = async () => {
  const response = await apiClient.get('/prescriptions');
  return response.data;
};

export const getPrescriptionDetail = async (id) => {
  const response = await apiClient.get(`/prescriptions/${id}`);
  return response.data;
};
