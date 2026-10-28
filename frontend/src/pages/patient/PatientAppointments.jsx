import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getBookings, cancelBooking } from '../../api/bookings';
import { initiatePayment } from '../../api/payments';
import {
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  XCircle,
  CreditCard,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles
} from 'lucide-react';

export const PatientAppointments = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const data = await getBookings();
      setBookings(data.bookings || []);
    } catch (err) {
      setError('Unable to load appointments.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const handleCancel = async (bookingId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment? Your slot will be released.')) {
      return;
    }
    setActionLoading(bookingId);
    setError('');
    setMessage('');
    try {
      await cancelBooking(bookingId, 'Patient requested cancellation');
      setMessage('Appointment cancelled successfully. Slot has been freed.');
      await fetchAppointments();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to cancel appointment.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleSimulatePayment = async (consultationId) => {
    setActionLoading(consultationId);
    setError('');
    setMessage('');
    try {
      const resp = await initiatePayment(consultationId, false);
      setMessage(`Payment of ₹${resp.payment.amount} processed successfully (Simulated Gateway).`);
      await fetchAppointments();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Payment simulation failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const getAppointmentStatusBadge = (status, isExpired) => {
    if (isExpired && status === 'BOOKED') {
      return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">Expired Reservation</span>;
    }
    switch (status) {
      case 'BOOKED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">Reserved</span>;
      case 'CONFIRMED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">Confirmed</span>;
      case 'IN_PROGRESS':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 animate-pulse">In Progress</span>;
      case 'COMPLETED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">Completed</span>;
      case 'CANCELLED':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-stone-200 text-stone-700">Cancelled</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-800">{status}</span>;
    }
  };

  const getPaymentStatusBadge = (payment, consultationStatus, isExpired) => {
    const payStatus = payment?.status;
    if (payStatus === 'COMPLETED' || consultationStatus === 'CONFIRMED' || consultationStatus === 'COMPLETED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
          <CheckCircle2 className="w-3 h-3" />
          <span>Paid</span>
        </span>
      );
    }
    if (isExpired && consultationStatus === 'BOOKED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-600">
          <XCircle className="w-3 h-3" />
          <span>Expired</span>
        </span>
      );
    }
    if (consultationStatus === 'CANCELLED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-600">
          <span>Not Billed</span>
        </span>
      );
    }
    if (payStatus === 'FAILED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
          <AlertCircle className="w-3 h-3" />
          <span>Payment Failed</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-900 border border-amber-200">
        <Clock className="w-3 h-3 text-amber-600" />
        <span>Payment Pending</span>
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading text-stone-900 tracking-tight">
            My Consultation Appointments
          </h1>
          <p className="text-xs sm:text-sm text-stone-600 mt-1">
            Review scheduled Ayurvedic sessions, complete simulation payments, or cancel upcoming bookings
          </p>
        </div>
        <button
          onClick={fetchAppointments}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-stone-200 bg-white text-stone-700 hover:bg-stone-50 text-xs font-semibold shadow-sm transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center gap-3 text-emerald-900 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600" />
          <div>{message}</div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-rose-900 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600" />
          <div>{error}</div>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-stone-100 animate-pulse" />
          ))}
        </div>
      ) : bookings.length === 0 ? (
        <div className="bg-white p-8 sm:p-12 rounded-2xl border border-stone-200 text-center max-w-md mx-auto space-y-4">
          <Calendar className="w-12 h-12 text-stone-400 mx-auto" />
          <h3 className="text-lg font-bold font-heading text-stone-900">No Appointments Scheduled</h3>
          <p className="text-xs text-stone-500 leading-relaxed">
            You currently have no active or previous telemedicine consultations on record.
          </p>
          <Link
            to="/doctors"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl herbal-gradient text-white text-xs font-semibold shadow-sm"
          >
            <span>Consult an Ayurvedic Doctor</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((booking) => {
            const start = new Date(booking.scheduled_start);
            const now = new Date();
            const isExpired = booking.status === 'BOOKED' && booking.expires_at && new Date(booking.expires_at) < now;
            const isPaid = booking.payment?.status === 'COMPLETED' || ['CONFIRMED', 'IN_PROGRESS', 'COMPLETED'].includes(booking.status);
            const canPay = booking.status === 'BOOKED' && !isExpired && !isPaid;
            const isEligibleCancel = ['BOOKED', 'CONFIRMED'].includes(booking.status) && !isExpired;

            return (
              <div
                key={booking.id}
                className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-4 sm:gap-6"
              >
                <div className="space-y-2 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                    <span className="font-mono text-xs font-bold text-stone-700 bg-stone-100 px-2.5 py-1 rounded-lg">
                      {booking.booking_reference}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] text-stone-500">Appointment:</span>
                      {getAppointmentStatusBadge(booking.status, isExpired)}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] text-stone-500">Payment:</span>
                      {getPaymentStatusBadge(booking.payment, booking.status, isExpired)}
                    </div>
                  </div>

                  <h3 className="text-lg font-bold font-heading text-stone-900">
                    Dr. {booking.doctor?.doctor_name}
                  </h3>
                  <div className="text-xs text-stone-500">
                    {booking.doctor?.specialization} &bull; Consultation Fee: ₹{booking.doctor?.consultation_fee}
                  </div>

                  <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs text-stone-600 pt-1">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-4 h-4 text-[#2B5B41]" />
                      <span>{start.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-[#2B5B41]" />
                      <span className="font-semibold">{start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    {booking.status === 'BOOKED' && booking.expires_at && !isExpired && (
                      <div className="flex items-center gap-1 text-amber-700 font-medium">
                        <Clock className="w-3.5 h-3.5 text-amber-600" />
                        <span>Hold expires at {new Date(booking.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    )}
                    {isExpired && (
                      <div className="flex items-center gap-1 text-rose-700 font-medium">
                        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                        <span>Reservation expired. Slot has been freed.</span>
                      </div>
                    )}
                  </div>

                  {booking.chief_complaint && (
                    <div className="text-xs text-stone-500 pt-1">
                      <span className="font-semibold text-stone-700">Complaint:</span> {booking.chief_complaint}
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto pt-2 lg:pt-0 border-t lg:border-t-0 border-stone-100">
                  {canPay && (
                    <button
                      onClick={() => handleSimulatePayment(booking.id)}
                      disabled={actionLoading !== null}
                      className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1.5 shadow-sm transition-colors disabled:opacity-50"
                    >
                      {actionLoading === booking.id ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Processing Payment...</span>
                        </>
                      ) : (
                        <>
                          <CreditCard className="w-3.5 h-3.5" />
                          <span>Pay Now (₹{booking.doctor?.consultation_fee})</span>
                        </>
                      )}
                    </button>
                  )}

                  {booking.status === 'COMPLETED' && (
                    <Link
                      to="/patient/prescriptions"
                      className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-stone-100 hover:bg-stone-200 text-stone-800 flex items-center gap-1.5 transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5 text-[#2B5B41]" />
                      <span>View Prescription</span>
                    </Link>
                  )}

                  {isEligibleCancel && (
                    <button
                      onClick={() => handleCancel(booking.id)}
                      disabled={actionLoading !== null}
                      className="px-4 py-2.5 rounded-xl text-xs font-semibold border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      {actionLoading === booking.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5" />
                      )}
                      <span>Cancel</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
};
