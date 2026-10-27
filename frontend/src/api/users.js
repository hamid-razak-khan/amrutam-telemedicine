import apiClient from './axios';

export const getUserProfile = async () => {
  const response = await apiClient.get('/users/me');
  return response.data;
};

export const updateUserProfile = async (profileData) => {
  const response = await apiClient.patch('/users/me', profileData);
  return response.data;
};
