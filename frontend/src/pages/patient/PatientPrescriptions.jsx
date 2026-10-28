import React, { useState, useEffect } from 'react';
import { getPrescriptions } from '../../api/prescriptions';
import {
  FileText,
  Calendar,
  User,
  Sparkles,
  Pill,
  Clock,
  AlertCircle,
  X,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

export const PatientPrescriptions = () => {
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPrescription, setSelectedPrescription] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPrescriptions = async () => {
      try {
        const data = await getPrescriptions();
        setPrescriptions(data.prescriptions || []);
      } catch (err) {
        setError('Failed to retrieve medical prescriptions.');
      } finally {
        setLoading(false);
      }
    };
    fetchPrescriptions();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-semibold mb-3">
          <FileText className="w-3.5 h-3.5 text-[#2B5B41]" />
          <span>Ayurvedic Clinical Records</span>
        </div>
        <h1 className="text-3xl font-bold font-heading text-stone-900 tracking-tight">
          My Prescriptions & Formulations
        </h1>
        <p className="text-sm text-stone-600 mt-1">
          Review structured herbal medication schedules, dosage instructions, and Ayurvedic dietary pathya
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600" />
          <div>{error}</div>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-32 rounded-2xl bg-stone-100 animate-pulse" />
          ))}
        </div>
      ) : prescriptions.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-stone-200 text-center max-w-md mx-auto space-y-4">
          <FileText className="w-12 h-12 text-stone-400 mx-auto" />
          <h3 className="text-lg font-bold font-heading text-stone-900">No Prescriptions Issued</h3>
          <p className="text-xs text-stone-500 leading-relaxed">
            Prescriptions will appear here automatically once your doctor completes a consultation.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {prescriptions.map((presc) => (
            <div
              key={presc.id}
              className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm hover:shadow-md transition-shadow space-y-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-mono text-[11px] font-bold text-stone-500 bg-stone-100 px-2 py-0.5 rounded">
                    {presc.consultation_reference}
                  </span>
                  <h3 className="text-lg font-bold font-heading text-stone-900 mt-2">
                    {presc.diagnosis}
                  </h3>
                  <div className="text-xs text-stone-500 mt-0.5">
                    Prescribed by Dr. {presc.doctor?.doctor_name}
                  </div>
                </div>

                <div className="text-right text-xs text-stone-400 font-medium">
                  {new Date(presc.created_at).toLocaleDateString()}
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-stone-100">
                <div className="text-xs font-semibold text-stone-700">Formulations Prescribed:</div>
                <div className="space-y-1.5">
                  {presc.medications?.slice(0, 2).map((med, idx) => (
                    <div key={idx} className="p-2.5 rounded-xl bg-stone-50 text-xs flex items-center justify-between">
                      <div className="font-semibold text-stone-800">{med.name}</div>
                      <div className="text-stone-500 text-[11px]">{med.dosage} &bull; {med.duration}</div>
                    </div>
                  ))}
                  {presc.medications?.length > 2 && (
                    <div className="text-[11px] text-[#2B5B41] font-medium">
                      +{presc.medications.length - 2} more herbal items
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-2">
                <button
                  onClick={() => setSelectedPrescription(presc)}
                  className="w-full py-2.5 rounded-xl bg-stone-100 hover:bg-[#2B5B41] hover:text-white text-stone-800 text-xs font-semibold transition-colors"
                >
                  View Complete Prescription Schedule
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Prescription Detail Modal */}
      {selectedPrescription && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/60 backdrop-blur-sm p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-4 sm:p-6 md:p-8 shadow-2xl border border-stone-200 relative animate-in fade-in duration-200 space-y-5 sm:space-y-6 max-h-[92vh] overflow-y-auto">
            
            <button
              onClick={() => setSelectedPrescription(null)}
              className="absolute right-4 top-4 sm:right-6 sm:top-6 p-1.5 rounded-xl text-stone-400 hover:bg-stone-100 hover:text-stone-700"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="border-b border-stone-100 pb-4">
              <div className="flex items-center gap-2 text-xs font-bold text-[#2B5B41] uppercase tracking-wider mb-1">
                <ShieldCheck className="w-4 h-4" />
                <span>Verified Ayurvedic Prescription</span>
              </div>
              <h2 className="text-2xl font-bold font-heading text-stone-900">
                {selectedPrescription.diagnosis}
              </h2>
              <div className="flex flex-wrap items-center gap-4 text-xs text-stone-500 mt-2">
                <span>Practitioner: <strong className="text-stone-700">Dr. {selectedPrescription.doctor?.doctor_name}</strong></span>
                <span>Date: <strong className="text-stone-700">{new Date(selectedPrescription.created_at).toLocaleDateString()}</strong></span>
                <span>Ref: <strong className="text-stone-700 font-mono">{selectedPrescription.consultation_reference}</strong></span>
              </div>
            </div>

            {/* Structured Medications Table */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-600 mb-3">
                Prescribed Herbal Formulations & Dosages
              </h4>
              <div className="overflow-x-auto border border-stone-200 rounded-xl">
                <table className="w-full min-w-[480px] text-left text-xs">
                  <thead className="bg-stone-50 border-b border-stone-200 text-stone-600 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Medicine / Churna</th>
                      <th className="py-2.5 px-3">Dosage</th>
                      <th className="py-2.5 px-3">Duration</th>
                      <th className="py-2.5 px-3">Instructions (Anupana)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {selectedPrescription.medications?.map((m, idx) => (
                      <tr key={idx} className="hover:bg-stone-50/50">
                        <td className="py-2.5 px-3 font-semibold text-stone-900">{m.name}</td>
                        <td className="py-2.5 px-3 text-stone-700">{m.dosage}</td>
                        <td className="py-2.5 px-3 text-stone-700">{m.duration}</td>
                        <td className="py-2.5 px-3 text-stone-600">{m.instructions || 'With warm water'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pathya / Dietary Guidelines */}
            {selectedPrescription.lifestyle_recommendations && (
              <div className="p-4 bg-emerald-50/70 border border-emerald-100 rounded-xl space-y-1">
                <div className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                  Pathya-Apathya (Dietary & Lifestyle Counseling)
                </div>
                <p className="text-xs text-emerald-950 leading-relaxed">
                  {selectedPrescription.lifestyle_recommendations}
                </p>
              </div>
            )}

            {/* Additional Doctor Notes & Follow up */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-stone-600 pt-2 border-t border-stone-100 gap-2">
              <div>
                {selectedPrescription.follow_up_date && (
                  <span>Scheduled Follow-up: <strong className="text-stone-900">{selectedPrescription.follow_up_date}</strong></span>
                )}
              </div>
              <button
                onClick={() => setSelectedPrescription(null)}
                className="px-5 py-2.5 rounded-xl bg-stone-800 hover:bg-stone-900 text-white text-xs font-semibold"
              >
                Close Prescription
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
