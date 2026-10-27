import apiClient from './axios';

export const initiatePayment = async (consultationId, simulateFailure = false, idempotencyKey = null) => {
  const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {};
  const response = await apiClient.post(
    '/payments',
    {
      consultation_id: consultationId,
      simulate_failure: simulateFailure,
    },
    { headers }
  );
  return response.data;
};

export const getPaymentDetail = async (id) => {
  const response = await apiClient.get(`/payments/${id}`);
  return response.data;
};
