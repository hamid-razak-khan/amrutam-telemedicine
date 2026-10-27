import apiClient from './axios';

export const getDoctors = async (params = {}) => {
  const response = await apiClient.get('/doctors', { params });
  return response.data;
};

export const getDoctorDetail = async (doctorId) => {
  const response = await apiClient.get(`/doctors/${doctorId}`);
  return response.data;
};

export const getDoctorAvailability = async (doctorId, date = null) => {
  const params = date ? { date } : {};
  const response = await apiClient.get(`/doctors/${doctorId}/availability`, { params });
  return response.data;
};

export const updateDoctorProfile = async (profileData) => {
  const response = await apiClient.patch('/doctors/me/profile', profileData);
  return response.data;
};

export const getDoctorMyAvailability = async () => {
  const response = await apiClient.get('/doctors/me/availability');
  return response.data;
};

export const createDoctorAvailabilitySlot = async (slotData) => {
  const response = await apiClient.post('/doctors/me/availability', slotData);
  return response.data;
};

export const cancelDoctorAvailabilitySlot = async (slotId) => {
  const response = await apiClient.patch(`/doctors/me/availability/${slotId}`, { status: 'CANCELLED' });
  return response.data;
};
