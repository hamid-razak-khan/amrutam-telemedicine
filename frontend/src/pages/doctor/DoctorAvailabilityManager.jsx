import React, { useState, useEffect } from 'react';
import { getDoctorMyAvailability, createDoctorAvailabilitySlot, cancelDoctorAvailabilitySlot } from '../../api/doctors';
import {
  Calendar,
  Clock,
  Plus,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Loader2,
  CalendarDays
} from 'lucide-react';

export const DoctorAvailabilityManager = () => {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formLoading, setFormLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Form State
  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('10:00');
  const [endTime, setEndTime] = useState('10:45');

  const fetchSlots = async () => {
    setLoading(true);
    try {
      const data = await getDoctorMyAvailability();
      setSlots(data.slots || []);
    } catch (err) {
      setError('Unable to load availability slots.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setDate(tomorrow.toISOString().split('T')[0]);
    fetchSlots();
  }, []);

  const handleCreateSlot = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!date || !startTime || !endTime) {
      setError('Please provide date, start time, and end time.');
      return;
    }

    const startAt = new Date(`${date}T${startTime}:00`);
    const endAt = new Date(`${date}T${endTime}:00`);

    if (endAt <= startAt) {
      setError('End time must be strictly after start time.');
      return;
    }

    if (startAt <= new Date()) {
      setError('Cannot schedule an availability slot in the past.');
      return;
    }

    setFormLoading(true);

    try {
      await createDoctorAvailabilitySlot({
        start_at: startAt.toISOString(),
        end_at: endAt.toISOString(),
      });
      setMessage('Availability slot created successfully.');
      await fetchSlots();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to create availability slot.');
    } finally {
      setFormLoading(false);
    }
  };

  const handleCancelSlot = async (slotId) => {
    if (!window.confirm('Are you sure you want to cancel this availability slot?')) {
      return;
    }
    setError('');
    setMessage('');
    try {
      await cancelDoctorAvailabilitySlot(slotId);
      setMessage('Slot marked as CANCELLED.');
      await fetchSlots();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to cancel slot.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-100 text-blue-900 text-xs font-semibold mb-3">
          <CalendarDays className="w-3.5 h-3.5 text-blue-700" />
          <span>Calendar Scheduling</span>
        </div>
        <h1 className="text-3xl font-bold font-heading text-stone-900 tracking-tight">
          Manage Availability Slots
        </h1>
        <p className="text-sm text-stone-600 mt-1">
          Open appointment slots on your calendar to allow patients to discover and book consultations
        </p>
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

      {/* Create New Slot Card */}
      <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
        <h3 className="text-base font-bold font-heading text-stone-900 flex items-center gap-2">
          <Plus className="w-4 h-4 text-[#2B5B41]" />
          <span>Add New Availability Slot</span>
        </h3>

        <form onSubmit={handleCreateSlot} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
              Date
            </label>
            <input
              type="date"
              required
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
              Start Time
            </label>
            <input
              type="time"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
              End Time
            </label>
            <input
              type="time"
              required
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={formLoading}
              className="w-full py-2.5 px-4 rounded-xl herbal-gradient text-white text-xs font-semibold shadow-sm hover:opacity-95 transition-all flex items-center justify-center gap-1.5"
            >
              {formLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              <span>Add Time Slot</span>
            </button>
          </div>
        </form>
      </div>

      {/* Existing Slots Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-stone-100 flex items-center justify-between">
          <h3 className="text-base font-bold font-heading text-stone-900">
            Scheduled Availability Calendar ({slots.length} total slots)
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-stone-400">Loading slots...</div>
        ) : slots.length === 0 ? (
          <div className="p-10 text-center text-xs text-stone-500">
            No availability slots configured yet. Use the form above to add your first consultation slot.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-stone-50 border-b border-stone-200 text-stone-600 uppercase font-semibold">
                <tr>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Start Time</th>
                  <th className="py-3 px-4">End Time</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {slots.map((slot) => {
                  const start = new Date(slot.start_at);
                  const end = new Date(slot.end_at);

                  return (
                    <tr key={slot.id} className="hover:bg-stone-50/50">
                      <td className="py-3 px-4 font-semibold text-stone-900">
                        {start.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="py-3 px-4 text-stone-700">
                        {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-3 px-4 text-stone-700">
                        {end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                          slot.status === 'AVAILABLE'
                            ? 'bg-emerald-100 text-emerald-800'
                            : slot.status === 'BOOKED'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-stone-100 text-stone-500'
                        }`}>
                          {slot.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {slot.status === 'AVAILABLE' && (
                          <button
                            onClick={() => handleCancelSlot(slot.id)}
                            className="text-rose-600 hover:text-rose-800 font-semibold text-xs"
                          >
                            Cancel Slot
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};
