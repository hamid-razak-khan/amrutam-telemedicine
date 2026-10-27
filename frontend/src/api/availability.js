import apiClient from './axios';

export const fetchDoctorSlots = async (doctorId, date) => {
  const params = date ? { date } : {};
  const response = await apiClient.get(`/doctors/${doctorId}/availability`, { params });
  return response.data;
};
