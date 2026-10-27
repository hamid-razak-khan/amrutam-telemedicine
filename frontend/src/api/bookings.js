import apiClient from './axios';

export const createBooking = async (bookingData, idempotencyKey) => {
  const key = idempotencyKey || ('amr_book_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9));
  const response = await apiClient.post('/bookings', bookingData, {
    headers: {
      'Idempotency-Key': key,
    },
  });
  return response.data;
};

export const getBookings = async (params = {}) => {
  const response = await apiClient.get('/bookings', { params });
  return response.data;
};

export const getBookingDetail = async (bookingId) => {
  const response = await apiClient.get(`/bookings/${bookingId}`);
  return response.data;
};

export const cancelBooking = async (bookingId, reason = 'Cancelled by user') => {
  const response = await apiClient.post(`/bookings/${bookingId}/cancel`, { reason });
  return response.data;
};
