import React, { useState, useEffect } from 'react';
import { getConsultations, startConsultation, completeConsultation } from '../../api/consultations';
import { createPrescription } from '../../api/prescriptions';
import {
  Stethoscope,
  Calendar,
  Clock,
  User,
  PlayCircle,
  CheckCircle2,
  FilePlus2,
  AlertCircle,
  Loader2,
  Plus,
  Trash2,
  X,
  FileText
} from 'lucide-react';

export const DoctorDashboard = () => {
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Prescription Modal State
  const [activePrescConsultation, setActivePrescConsultation] = useState(null);
  const [diagnosis, setDiagnosis] = useState('');
  const [lifestyle, setLifestyle] = useState('');
  const [followUpDate, setFollowUpDate] = useState('');
  const [medications, setMedications] = useState([
    { name: 'Amrutam Kuntal Care Herbal Malt', dosage: '1 tbsp twice daily', duration: '15 days', instructions: 'After meals with warm milk' },
  ]);
  const [prescLoading, setPrescLoading] = useState(false);
  const [prescError, setPrescError] = useState('');

  const fetchConsultations = async () => {
    setLoading(true);
    try {
      const data = await getConsultations();
      setConsultations(data.consultations || []);
    } catch (err) {
      setError('Unable to load clinical consultations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsultations();
  }, []);

  const handleStart = async (id) => {
    setActionLoading(id);
    setError('');
    setMessage('');
    try {
      await startConsultation(id, 'Started by doctor');
      setMessage('Consultation is now IN_PROGRESS.');
      await fetchConsultations();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to start consultation.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleComplete = async (id) => {
    setActionLoading(id);
    setError('');
    setMessage('');
    try {
      await completeConsultation(id, 'Consultation completed successfully by doctor.');
      setMessage('Consultation marked as COMPLETED.');
      await fetchConsultations();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to complete consultation.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleAddMedicationRow = () => {
    setMedications([...medications, { name: '', dosage: '', duration: '', instructions: '' }]);
  };

  const handleRemoveMedicationRow = (idx) => {
    setMedications(medications.filter((_, i) => i !== idx));
  };

  const handleMedChange = (idx, field, val) => {
    const updated = [...medications];
    updated[idx][field] = val;
    setMedications(updated);
  };

  const handleOpenPrescriptionModal = (consultation) => {
    setActivePrescConsultation(consultation);
    setDiagnosis('');
    setLifestyle('');
    setFollowUpDate('');
    setPrescError('');
    setMedications([
      { name: 'Triphala Churna', dosage: '1 tsp at bedtime', duration: '14 days', instructions: 'Take with warm water' }
    ]);
  };

  const handleSubmitPrescription = async (e) => {
    e.preventDefault();
    if (!diagnosis) {
      setPrescError('Diagnosis is required.');
      return;
    }
    if (medications.some((m) => !m.name.trim())) {
      setPrescError('All medication entries must have a valid medicine name.');
      return;
    }

    setPrescLoading(true);
    setPrescError('');

    try {
      const payload = {
        diagnosis,
        medications,
        lifestyle_recommendations: lifestyle,
        follow_up_date: followUpDate || null,
        additional_notes: 'Generated via Doctor Clinical Workspace'
      };

      await createPrescription(activePrescConsultation.id, payload);
      setMessage('Prescription generated and securely assigned to patient profile.');
      setActivePrescConsultation(null);
      await fetchConsultations();
    } catch (err) {
      setPrescError(err.response?.data?.error?.message || 'Failed to issue prescription.');
    } finally {
      setPrescLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-100 text-blue-900 text-xs font-semibold mb-3">
          <Stethoscope className="w-3.5 h-3.5 text-blue-700" />
          <span>Doctor Clinical Workspace</span>
        </div>
        <h1 className="text-3xl font-bold font-heading text-stone-900 tracking-tight">
          Clinical Appointments & Consultations
        </h1>
        <p className="text-sm text-stone-600 mt-1">
          Manage patient queue, initiate telemedicine sessions, mark completions, and issue structured digital prescriptions
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

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-stone-100 animate-pulse" />
          ))}
        </div>
      ) : consultations.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-stone-200 text-center max-w-md mx-auto space-y-4">
          <Stethoscope className="w-12 h-12 text-stone-400 mx-auto" />
          <h3 className="text-lg font-bold font-heading text-stone-900">No Patient Consultations Assigned</h3>
          <p className="text-xs text-stone-500 leading-relaxed">
            Ensure your schedule has open availability slots so patients can discover and book consultations with you.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {consultations.map((consultation) => {
            const start = new Date(consultation.scheduled_start);
            const canStart = ['BOOKED', 'CONFIRMED'].includes(consultation.status);
            const canComplete = consultation.status === 'IN_PROGRESS';
            const canPrescribe = ['IN_PROGRESS', 'COMPLETED'].includes(consultation.status);

            return (
              <div
                key={consultation.id}
                className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="font-mono text-xs font-bold text-stone-700 bg-stone-100 px-2.5 py-1 rounded-lg">
                      {consultation.booking_reference}
                    </span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      consultation.status === 'IN_PROGRESS'
                        ? 'bg-purple-100 text-purple-800 animate-pulse'
                        : consultation.status === 'COMPLETED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : consultation.status === 'CANCELLED'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {consultation.status}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold font-heading text-stone-900">
                    Patient: {consultation.patient?.full_name || consultation.patient?.email}
                  </h3>

                  <div className="flex items-center gap-4 text-xs text-stone-600">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-4 h-4 text-[#2B5B41]" />
                      <span>{start.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-[#2B5B41]" />
                      <span className="font-semibold">{start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>

                  {consultation.chief_complaint && (
                    <div className="text-xs text-stone-600 bg-amber-50/70 p-2.5 rounded-xl border border-amber-100/80">
                      <strong className="text-amber-900">Patient Symptoms:</strong> {consultation.chief_complaint}
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2.5 md:self-center">
                  {canStart && (
                    <button
                      onClick={() => handleStart(consultation.id)}
                      disabled={actionLoading === consultation.id}
                      className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1.5 shadow-sm transition-colors"
                    >
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>Start Consultation</span>
                    </button>
                  )}

                  {canComplete && (
                    <button
                      onClick={() => handleComplete(consultation.id)}
                      disabled={actionLoading === consultation.id}
                      className="px-4 py-2 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white flex items-center gap-1.5 shadow-sm transition-colors"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Complete Consultation</span>
                    </button>
                  )}

                  {canPrescribe && (
                    <button
                      onClick={() => handleOpenPrescriptionModal(consultation)}
                      className="px-4 py-2 rounded-xl text-xs font-semibold border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 flex items-center gap-1.5 transition-colors"
                    >
                      <FilePlus2 className="w-3.5 h-3.5 text-[#2B5B41]" />
                      <span>Issue Prescription</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Prescription Writing Modal */}
      {activePrescConsultation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-8 shadow-2xl border border-stone-200 relative animate-in fade-in duration-200 space-y-6">
            
            <button
              onClick={() => setActivePrescConsultation(null)}
              className="absolute right-6 top-6 p-1.5 rounded-xl text-stone-400 hover:bg-stone-100"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <div className="text-xs font-bold text-[#2B5B41] uppercase tracking-wider">
                Clinical Prescription Writer
              </div>
              <h2 className="text-2xl font-bold font-heading text-stone-900">
                Prescribe Formulation: {activePrescConsultation.patient?.full_name}
              </h2>
              <div className="text-xs text-stone-500 font-mono mt-0.5">
                Ref: {activePrescConsultation.booking_reference}
              </div>
            </div>

            {prescError && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2 text-rose-800 text-xs">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600 mt-0.5" />
                <div>{prescError}</div>
              </div>
            )}

            <form onSubmit={handleSubmitPrescription} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                  Ayurvedic / Clinical Diagnosis
                </label>
                <input
                  type="text"
                  required
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="e.g. Mandagni with Pitta-Kapha aggravation"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                />
              </div>

              {/* Dynamic Medications List */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-stone-600">
                    Herbal Medicines & Formulations
                  </label>
                  <button
                    type="button"
                    onClick={handleAddMedicationRow}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-[#2B5B41] hover:underline"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Item</span>
                  </button>
                </div>

                <div className="space-y-3">
                  {medications.map((med, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-stone-50 border border-stone-200 flex flex-col sm:flex-row gap-2 items-center">
                      <input
                        type="text"
                        placeholder="Medicine Name (e.g. Ashwagandha)"
                        value={med.name}
                        onChange={(e) => handleMedChange(idx, 'name', e.target.value)}
                        className="w-full sm:w-1/3 px-3 py-1.5 rounded-lg border border-stone-200 text-xs bg-white"
                      />
                      <input
                        type="text"
                        placeholder="Dosage (e.g. 1 tsp twice)"
                        value={med.dosage}
                        onChange={(e) => handleMedChange(idx, 'dosage', e.target.value)}
                        className="w-full sm:w-1/4 px-3 py-1.5 rounded-lg border border-stone-200 text-xs bg-white"
                      />
                      <input
                        type="text"
                        placeholder="Duration (e.g. 14 days)"
                        value={med.duration}
                        onChange={(e) => handleMedChange(idx, 'duration', e.target.value)}
                        className="w-full sm:w-1/4 px-3 py-1.5 rounded-lg border border-stone-200 text-xs bg-white"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveMedicationRow(idx)}
                        className="p-1.5 text-stone-400 hover:text-rose-600 self-end sm:self-center"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Lifestyle & Pathya */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                  Pathya-Apathya (Dietary & Lifestyle Advice)
                </label>
                <textarea
                  rows={2}
                  value={lifestyle}
                  onChange={(e) => setLifestyle(e.target.value)}
                  placeholder="Dietary rules: avoid cold liquids, drink warm water with ginger, dinner before 8pm..."
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                  Scheduled Follow-up Date (Optional)
                </label>
                <input
                  type="date"
                  value={followUpDate}
                  onChange={(e) => setFollowUpDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                />
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setActivePrescConsultation(null)}
                  className="px-4 py-2.5 rounded-xl border border-stone-200 text-xs font-semibold text-stone-700 hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={prescLoading}
                  className="px-6 py-2.5 rounded-xl herbal-gradient text-white text-xs font-semibold shadow-sm hover:opacity-95"
                >
                  {prescLoading ? 'Assigning prescription...' : 'Issue Prescription'}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
};
