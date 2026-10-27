import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDoctors } from '../api/doctors';
import {
  Sparkles,
  ShieldCheck,
  CalendarCheck,
  FileCheck2,
  Lock,
  ArrowRight,
  Star,
  Clock,
  Search,
  CheckCircle2,
  Stethoscope
} from 'lucide-react';

export const Home = () => {
  const [featuredDoctors, setFeaturedDoctors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFeatured = async () => {
      try {
        const data = await getDoctors();
        setFeaturedDoctors(data.results ? data.results.slice(0, 3) : []);
      } catch (e) {
        // Fallback
      } finally {
        setLoading(false);
      }
    };
    fetchFeatured();
  }, []);

  return (
    <div className="space-y-20 pb-20">
      
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-24 md:pt-20 md:pb-32">
        <div className="absolute inset-0 bg-gradient-to-b from-[#EBF3ED]/60 via-[#FAF8F5] to-[#FAF8F5] -z-10" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-100/80 border border-emerald-200 text-xs font-semibold text-emerald-900 mb-8 animate-fade-in">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>Pioneering Ayurvedic Telemedicine & Classical Care</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold font-heading text-[#1C3E2D] tracking-tight max-w-4xl mx-auto leading-[1.15] mb-6">
            Ancient Ayurvedic Wisdom. <br />
            <span className="italic font-normal text-[#2B5B41]">Modern Clinical Precision.</span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg text-stone-600 mb-10 leading-relaxed font-sans">
            Connect directly with verified Ayurvedic Vaidyas. Enjoy guaranteed zero double-booking, transaction-safe appointments, and authentic structured herbal prescriptions.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/doctors"
              className="w-full sm:w-auto px-8 py-4 rounded-xl text-white herbal-gradient font-semibold shadow-lg shadow-emerald-900/20 hover:opacity-95 transition-all flex items-center justify-center gap-2 text-base"
            >
              <span>Consult an Ayurvedic Doctor</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/register"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-white border border-stone-200 text-stone-800 font-semibold hover:bg-stone-50 transition-all text-base shadow-sm"
            >
              Create Patient Account
            </Link>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto pt-10 border-t border-stone-200/80">
            <div>
              <div className="text-3xl font-bold text-[#1C3E2D] font-heading">100%</div>
              <div className="text-xs text-stone-500 font-medium mt-1">Verified AYUSH Doctors</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-[#1C3E2D] font-heading">Zero</div>
              <div className="text-xs text-stone-500 font-medium mt-1">Double-Booking Races</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-[#1C3E2D] font-heading">Strict</div>
              <div className="text-xs text-stone-500 font-medium mt-1">Multi-Tenant Privacy</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-[#1C3E2D] font-heading">100k</div>
              <div className="text-xs text-stone-500 font-medium mt-1">Target Scalability Ready</div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Doctors Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[#2B5B41] mb-2">Expert Consultations</div>
            <h2 className="text-3xl sm:text-4xl font-bold text-stone-900 font-heading">
              Our Senior Ayurvedic Practitioners
            </h2>
          </div>
          <Link
            to="/doctors"
            className="mt-4 md:mt-0 inline-flex items-center gap-1.5 text-sm font-semibold text-[#2B5B41] hover:underline"
          >
            <span>View All Doctors & Availability</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 rounded-2xl bg-stone-100 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {featuredDoctors.map((doc) => (
              <div
                key={doc.id}
                className="bg-white rounded-2xl p-6 border border-stone-200/90 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl bg-emerald-50 text-[#2B5B41] flex items-center justify-center font-bold text-lg font-heading">
                      Dr
                    </div>
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verified
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-stone-900 font-heading mb-1">
                    {doc.doctor_name}
                  </h3>
                  <div className="text-xs font-semibold text-[#2B5B41] mb-3">
                    {doc.credentials}
                  </div>
                  <div className="text-sm font-medium text-stone-700 mb-2">
                    {doc.specialization}
                  </div>
                  <p className="text-xs text-stone-500 line-clamp-3 leading-relaxed mb-6">
                    {doc.biography}
                  </p>
                </div>

                <div className="pt-4 border-t border-stone-100 flex items-center justify-between">
                  <div>
                    <div className="text-[11px] text-stone-400 font-medium">Consultation Fee</div>
                    <div className="text-lg font-bold text-stone-900">₹{doc.consultation_fee}</div>
                  </div>
                  <Link
                    to={`/doctors?select=${doc.id}`}
                    className="px-4 py-2 rounded-xl text-xs font-semibold herbal-gradient text-white hover:opacity-90 transition-opacity"
                  >
                    Select Slot
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Engineering & Platform Pillars */}
      <section className="bg-white border-y border-stone-200/80 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-stone-900 font-heading mb-4">
              Engineered for Clinical Integrity & Reliability
            </h2>
            <p className="text-stone-600 text-base leading-relaxed">
              Every appointment booking is backed by database-level concurrency control, preventing appointment collisions and ensuring absolute tenant privacy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-8 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
              <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center mb-6">
                <Lock className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-stone-900 font-heading mb-2">
                Pessimistic Locking & Idempotency
              </h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Atomic database transactions with <code className="text-xs bg-stone-200 px-1 py-0.5 rounded">select_for_update()</code> ensure that simultaneous booking attempts never result in double bookings.
              </p>
            </div>

            <div className="p-8 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center mb-6">
                <FileCheck2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-stone-900 font-heading mb-2">
                Structured Ayurvedic Prescriptions
              </h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Doctors issue structured herbal formulations with explicit dosages, durations, and dietary pathya guidelines. Patient access is strictly isolated.
              </p>
            </div>

            <div className="p-8 rounded-2xl bg-[#FAF8F5] border border-stone-200/80">
              <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-800 flex items-center justify-center mb-6">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-stone-900 font-heading mb-2">
                Append-Only Audit Logging
              </h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Every authentication, booking, consultation state transition, and payment event is permanently logged with sanitized metadata and request tracing.
              </p>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
};
