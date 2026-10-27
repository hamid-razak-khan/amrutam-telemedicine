import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getDoctors, getDoctorAvailability } from '../../api/doctors';
import { createBooking } from '../../api/bookings';
import { useAuth } from '../../context/AuthContext';
import {
  Search,
  Filter,
  CheckCircle2,
  Calendar,
  Clock,
  Sparkles,
  X,
  AlertCircle,
  Loader2,
  ArrowRight,
  ShieldCheck,
  CreditCard
} from 'lucide-react';

export const DoctorsDirectory = () => {
  const [searchParams] = useSearchParams();
  const { user, isAuthenticated } = useAuth();

  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [maxFee, setMaxFee] = useState('');

  // Booking Modal State
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState(null);

  // Cached idempotency key for retries
  const [idempotencyKey, setIdempotencyKey] = useState('');

  const fetchDoctors = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (specialization) params.specialization = specialization;
      if (maxFee) params.max_fee = maxFee;

      const data = await getDoctors(params);
      const results = data.results || data;
      setDoctors(results);

      // Auto-open modal if select param passed
      const selectId = searchParams.get('select');
      if (selectId && results.length > 0) {
        const found = results.find((d) => d.id === selectId);
        if (found) handleOpenBooking(found);
      }
    } catch (e) {
      //
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctors();
  }, [specialization]);

  const handleOpenBooking = async (doctor) => {
    setSelectedDoctor(doctor);
    setSelectedSlot(null);
    setBookingError('');
    setBookingSuccess(null);
    setChiefComplaint('');
    // Generate fresh idempotency key for new logical booking
    setIdempotencyKey('amr_book_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9));
    setSlotsLoading(true);

    try {
      const data = await getDoctorAvailability(doctor.id);
      setSlots(data.slots || []);
    } catch (err) {
      setBookingError('Unable to load availability slots. Please try again.');
    } finally {
      setSlotsLoading(false);
    }
  };

  const handleConfirmBooking = async () => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }
    if (!selectedSlot) {
      setBookingError('Please choose an available appointment slot.');
      return;
    }

    setBookingLoading(true);
    setBookingError('');

    try {
      const payload = {
        slot_id: selectedSlot.id,
        chief_complaint: chiefComplaint,
      };

      // Submit booking with consistent idempotency key
      const response = await createBooking(payload, idempotencyKey);
      setBookingSuccess(response.booking);
    } catch (err) {
      const errCode = err.response?.data?.error?.code;
      const errMsg = err.response?.data?.error?.message || 'Failed to complete appointment booking.';

      if (errCode === 'SLOT_UNAVAILABLE' || err.response?.status === 409) {
        setBookingError('This time slot was just booked by another patient or is no longer available. Please select another slot.');
        // Refresh available slots
        const data = await getDoctorAvailability(selectedDoctor.id);
        setSlots(data.slots || []);
        setSelectedSlot(null);
      } else {
        setBookingError(errMsg);
      }
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5 text-amber-600" />
          <span>AYUSH Verified Practitioners</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold font-heading text-stone-900 tracking-tight">
          Consult Verified Ayurvedic Specialists
        </h1>
        <p className="text-sm text-stone-600 mt-1 max-w-2xl leading-relaxed">
          Book authenticated one-on-one telemedicine consultations. Select a verified doctor to inspect their real-time calendar and reserve your slot.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 sm:p-5 rounded-2xl border border-stone-200/90 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchDoctors()}
            placeholder="Search by doctor name or condition..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
          />
          <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <select
            value={specialization}
            onChange={(e) => setSpecialization(e.target.value)}
            className="px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50 text-stone-700"
          >
            <option value="">All Specializations</option>
            <option value="Kayachikitsa">Kayachikitsa & Panchakarma</option>
            <option value="Dermatology">Dermatology & Hair</option>
            <option value="Joint Care">Musculoskeletal & Joint Care</option>
            <option value="Metabolic">Metabolic & Hormonal Health</option>
          </select>

          <input
            type="number"
            value={maxFee}
            onChange={(e) => setMaxFee(e.target.value)}
            placeholder="Max fee (₹)"
            className="w-28 px-3 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
          />

          <button
            onClick={fetchDoctors}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold herbal-gradient text-white shadow-sm hover:opacity-95 transition-opacity"
          >
            Apply Filters
          </button>
        </div>
      </div>

      {/* Doctors Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-64 rounded-2xl bg-stone-100 animate-pulse" />
          ))}
        </div>
      ) : doctors.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-stone-200 text-center max-w-lg mx-auto">
          <AlertCircle className="w-10 h-10 text-stone-400 mx-auto mb-3" />
          <h3 className="text-lg font-bold font-heading text-stone-800">No Doctors Found</h3>
          <p className="text-xs text-stone-500 mt-1">Try resetting your search query or fee filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-2xl p-6 border border-stone-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl herbal-gradient text-white flex items-center justify-center font-bold text-lg font-heading shadow-sm">
                    {doc.doctor_name.replace('Dr. ', '').charAt(0)}
                  </div>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-100">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Verified
                  </span>
                </div>

                <h3 className="text-lg font-bold font-heading text-stone-900 mb-0.5">
                  {doc.doctor_name}
                </h3>
                <div className="text-xs font-semibold text-[#2B5B41] mb-2">{doc.credentials}</div>
                <div className="inline-block px-2.5 py-0.5 rounded-lg bg-stone-100 text-xs font-medium text-stone-700 mb-3">
                  {doc.specialization}
                </div>
                <p className="text-xs text-stone-500 line-clamp-3 leading-relaxed mb-4">
                  {doc.biography}
                </p>
                <div className="text-xs text-stone-500 font-medium">
                  Experience: <span className="text-stone-800 font-semibold">{doc.years_of_experience} years</span>
                </div>
              </div>

              <div className="pt-5 border-t border-stone-100 mt-4 flex items-center justify-between">
                <div>
                  <div className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">Fee</div>
                  <div className="text-xl font-bold text-stone-900">₹{doc.consultation_fee}</div>
                </div>
                <button
                  onClick={() => handleOpenBooking(doc)}
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold herbal-gradient text-white shadow-sm hover:opacity-95 transition-all flex items-center gap-1.5"
                >
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Book Slot</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Booking Modal */}
      {selectedDoctor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-stone-200 relative animate-in fade-in zoom-in-95 duration-200">
            
            <button
              onClick={() => setSelectedDoctor(null)}
              className="absolute right-4 top-4 p-1.5 rounded-xl text-stone-400 hover:bg-stone-100 hover:text-stone-700 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {bookingSuccess ? (
              <div className="text-center py-6 space-y-4">
                <div className="w-14 h-14 bg-emerald-100 text-emerald-800 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold font-heading text-stone-900">
                  Appointment Confirmed!
                </h3>
                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 text-left space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-stone-500 font-medium">Booking Reference:</span>
                    <span className="font-mono font-bold text-emerald-950">{bookingSuccess.booking_reference}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500 font-medium">Doctor:</span>
                    <span className="font-semibold text-stone-900">Dr. {bookingSuccess.doctor?.doctor_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500 font-medium">Scheduled Time:</span>
                    <span className="font-semibold text-stone-900">
                      {new Date(bookingSuccess.scheduled_start).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500 font-medium">Status:</span>
                    <span className="font-bold text-emerald-800 uppercase">{bookingSuccess.status}</span>
                  </div>
                </div>

                <div className="pt-2 flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={() => {
                      setSelectedDoctor(null);
                      window.location.href = '/patient/appointments';
                    }}
                    className="flex-1 py-3 px-4 rounded-xl herbal-gradient text-white text-xs font-semibold shadow-sm"
                  >
                    View in Appointments
                  </button>
                  <button
                    onClick={() => setSelectedDoctor(null)}
                    className="py-3 px-4 rounded-xl border border-stone-200 text-stone-700 text-xs font-semibold hover:bg-stone-50"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-[#2B5B41]">
                    Schedule Consultation
                  </div>
                  <h3 className="text-xl font-bold font-heading text-stone-900">
                    {selectedDoctor.doctor_name}
                  </h3>
                  <div className="text-xs text-stone-500">
                    {selectedDoctor.specialization} &bull; ₹{selectedDoctor.consultation_fee} per session
                  </div>
                </div>

                {bookingError && (
                  <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2 text-rose-800 text-xs">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600 mt-0.5" />
                    <div>{bookingError}</div>
                  </div>
                )}

                {/* Available Slots Selector */}
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-2">
                    Select Available Time Slot
                  </label>
                  
                  {slotsLoading ? (
                    <div className="py-8 flex items-center justify-center gap-2 text-xs text-stone-500">
                      <Loader2 className="w-4 h-4 animate-spin text-[#2B5B41]" />
                      <span>Loading real-time availability slots...</span>
                    </div>
                  ) : slots.length === 0 ? (
                    <div className="p-6 bg-stone-50 rounded-xl text-center text-xs text-stone-500 border border-stone-200">
                      No open slots found for this doctor in the next 7 days.
                    </div>
                  ) : (
                    <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                      {slots.map((slot) => {
                        const start = new Date(slot.start_at);
                        const end = new Date(slot.end_at);
                        const isSelected = selectedSlot?.id === slot.id;

                        return (
                          <div
                            key={slot.id}
                            onClick={() => setSelectedSlot(slot)}
                            className={`p-3 rounded-xl border text-xs cursor-pointer flex items-center justify-between transition-all ${
                              isSelected
                                ? 'border-[#2B5B41] bg-emerald-50/70 text-[#1C3E2D] font-semibold ring-1 ring-[#2B5B41]'
                                : 'border-stone-200 hover:border-emerald-300 bg-white text-stone-700'
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <Clock className={`w-4 h-4 ${isSelected ? 'text-[#2B5B41]' : 'text-stone-400'}`} />
                              <span>{start.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</span>
                              <span className="font-bold">{start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                              <span>-</span>
                              <span>{end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                            <span className="text-[10px] uppercase font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
                              Available
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Chief Complaint / Health Notes */}
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                    Chief Complaint / Primary Symptoms (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={chiefComplaint}
                    onChange={(e) => setChiefComplaint(e.target.value)}
                    placeholder="Briefly describe your symptoms, digestion, or primary concern..."
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                  />
                </div>

                <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 flex items-center justify-between text-xs text-stone-600">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-[#2B5B41]" />
                    <span>Idempotent Transaction Guarantee</span>
                  </div>
                  <span className="font-mono text-[10px] text-stone-400">
                    {idempotencyKey.substring(0, 14)}...
                  </span>
                </div>

                <div className="pt-2">
                  <button
                    onClick={handleConfirmBooking}
                    disabled={bookingLoading || !selectedSlot}
                    className="w-full py-3.5 px-4 rounded-xl herbal-gradient text-white text-sm font-semibold shadow-md shadow-emerald-900/10 hover:opacity-95 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {bookingLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Acquiring transaction lock...</span>
                      </>
                    ) : (
                      <>
                        <span>Confirm & Reserve Appointment</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
};
