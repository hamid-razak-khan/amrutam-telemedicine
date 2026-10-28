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

// Admin Doctor Approval Operations
export const getAdminDoctorApplications = async (status = null) => {
  const params = status ? { status } : {};
  const response = await apiClient.get('/admin/doctors', { params });
  return response.data;
};

export const approveDoctor = async (doctorId) => {
  const response = await apiClient.post(`/admin/doctors/${doctorId}/approve`);
  return response.data;
};

export const rejectDoctor = async (doctorId, reason) => {
  const response = await apiClient.post(`/admin/doctors/${doctorId}/reject`, { reason });
  return response.data;
};

export const removeDoctor = async (doctorId, reason = 'No longer working with the organization') => {
  const response = await apiClient.post(`/admin/doctors/${doctorId}/remove`, { reason });
  return response.data;
};


