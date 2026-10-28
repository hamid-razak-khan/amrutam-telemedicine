import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDoctors } from '../api/doctors';
import {
  ArrowRight,
  ShieldCheck,
  Calendar,
  Lock,
  CheckCircle2,
  Stethoscope,
  Search,
  CalendarCheck,
  Users,
  FileCheck2,
  AlertCircle
} from 'lucide-react';

export const Home = () => {
  const [featuredDoctors, setFeaturedDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFeatured = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDoctors();
      const docs = data.results || (Array.isArray(data) ? data : []);
      // Display approved practitioners if status provided
      const approved = docs.filter(
        (d) => !d.verification_status || d.verification_status === 'APPROVED' || d.verification_status === 'VERIFIED'
      );
      // Display up to 4 featured doctors
      setFeaturedDoctors(approved.slice(0, 4));
    } catch (err) {
      console.error('Error fetching featured doctors:', err);
      setError('Unable to load doctor profiles at this time. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeatured();
  }, []);

  return (
    <div className="space-y-20 sm:space-y-24 pb-20">
      
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24">
        <div className="absolute inset-0 bg-gradient-to-b from-[#EBF3ED]/70 via-[#FAF8F5] to-[#FAF8F5] -z-10" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            
            {/* Main Heading */}
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold font-heading text-stone-900 tracking-tight leading-tight mb-6">
              Healthcare Made Simpler, <br className="hidden sm:inline" />
              <span className="text-[#2B5B41]">Care Made Closer</span>
            </h1>

            {/* Description */}
            <p className="max-w-2xl mx-auto text-base sm:text-lg text-stone-600 mb-8 sm:mb-10 leading-relaxed font-sans">
              Find trusted healthcare professionals, book online consultations, and manage your healthcare journey in one place.
            </p>

            {/* Call to Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
              <Link
                to="/doctors"
                id="hero-find-doctor-btn"
                className="w-full sm:w-auto px-7 py-3.5 rounded-xl text-white bg-[#2B5B41] hover:bg-[#224834] font-semibold shadow-sm transition-all flex items-center justify-center gap-2 text-sm sm:text-base"
              >
                <span>Find a Doctor</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/doctors"
                id="hero-book-consult-btn"
                className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-white border border-stone-300 text-stone-800 font-semibold hover:bg-stone-50 transition-all text-sm sm:text-base shadow-xs flex items-center justify-center"
              >
                Book Consultation
              </Link>
            </div>

            {/* Three Highlights */}
            <div className="mt-12 sm:mt-16 flex flex-wrap items-center justify-center gap-6 sm:gap-12 pt-8 border-t border-stone-200/80 text-stone-700 text-xs sm:text-sm font-medium">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-[#2B5B41]">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <span>Verified Doctors</span>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-[#2B5B41]">
                  <Calendar className="w-4 h-4" />
                </div>
                <span>Easy Appointment Booking</span>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-[#2B5B41]">
                  <Lock className="w-4 h-4" />
                </div>
                <span>Secure Patient Accounts</span>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 2. FEATURED DOCTORS SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-stone-900 font-heading tracking-tight">
            Meet Our Doctors
          </h2>
          <p className="text-stone-600 text-xs sm:text-sm mt-2">
            Browse verified practitioners available for online consultation.
          </p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-80 rounded-2xl bg-white border border-stone-200 p-6 flex flex-col justify-between animate-pulse">
                <div className="space-y-4">
                  <div className="w-12 h-12 bg-stone-200 rounded-xl" />
                  <div className="h-4 bg-stone-200 rounded w-3/4" />
                  <div className="h-3 bg-stone-200 rounded w-1/2" />
                  <div className="h-3 bg-stone-200 rounded w-full" />
                </div>
                <div className="h-10 bg-stone-200 rounded-xl" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-white p-8 rounded-2xl border border-stone-200 text-center max-w-md mx-auto shadow-xs space-y-3">
            <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
            <p className="text-sm text-stone-700">{error}</p>
            <button
              onClick={fetchFeatured}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-800 transition-colors"
            >
              Retry Loading Doctors
            </button>
          </div>
        ) : featuredDoctors.length === 0 ? (
          <div className="bg-white p-10 rounded-2xl border border-stone-200 text-center max-w-md mx-auto shadow-xs">
            <Stethoscope className="w-10 h-10 text-stone-400 mx-auto mb-3" />
            <h3 className="text-base font-bold font-heading text-stone-800">No Doctors Currently Listed</h3>
            <p className="text-xs text-stone-500 mt-1">
              Check back soon or explore our doctor directory.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredDoctors.map((doc) => {
              const isDemo =
                doc.credentials?.toLowerCase().includes('demonstration') ||
                doc.biography?.toLowerCase().includes('demonstration') ||
                doc.user?.email?.includes('example.com');

              return (
                <div
                  key={doc.id}
                  className="bg-white rounded-2xl p-5 sm:p-6 border border-stone-200 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between mb-4">
                      <div className="w-12 h-12 rounded-xl bg-emerald-50 text-[#2B5B41] border border-emerald-100 flex items-center justify-center font-bold text-lg font-heading">
                        {doc.doctor_name?.replace('Dr. ', '').charAt(0) || 'D'}
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-100">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          Approved
                        </span>
                        {isDemo && (
                          <span className="text-[10px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            Demo Profile
                          </span>
                        )}
                      </div>
                    </div>

                    <h3 className="text-base sm:text-lg font-bold text-stone-900 font-heading mb-1 line-clamp-1">
                      {doc.doctor_name}
                    </h3>
                    <div className="text-xs font-semibold text-[#2B5B41] mb-2 line-clamp-1">
                      {doc.specialization}
                    </div>

                    <div className="text-xs text-stone-500 mb-2 line-clamp-1 font-medium">
                      {doc.credentials}
                    </div>

                    <div className="text-xs text-stone-500 mb-4">
                      Experience: <span className="text-stone-800 font-semibold">{doc.years_of_experience || 5} years</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-stone-100">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs text-stone-500 font-medium">Consultation Fee</span>
                      <span className="text-base font-bold text-stone-900">₹{doc.consultation_fee}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <Link
                        to={`/doctors?select=${doc.id}`}
                        className="py-2 px-2.5 rounded-xl text-center text-xs font-semibold border border-stone-200 text-stone-700 hover:bg-stone-50 transition-colors"
                      >
                        View Profile
                      </Link>
                      <Link
                        to={`/doctors?select=${doc.id}`}
                        className="py-2 px-2.5 rounded-xl text-center text-xs font-semibold bg-[#2B5B41] hover:bg-[#224834] text-white shadow-xs transition-colors"
                      >
                        Book Appointment
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* View All Doctors Button */}
        <div className="mt-10 text-center">
          <Link
            to="/doctors"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-stone-300 bg-white text-stone-800 text-sm font-semibold hover:bg-stone-50 shadow-xs transition-all"
          >
            <span>View All Doctors</span>
            <ArrowRight className="w-4 h-4 text-stone-600" />
          </Link>
        </div>
      </section>

      {/* 3. KEY FEATURES SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold font-heading text-stone-900 tracking-tight">
            Everything You Need for Better Care
          </h2>
          <p className="text-stone-600 text-xs sm:text-sm mt-2">
            A simple, integrated platform designed for seamless healthcare management.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Feature 1 */}
          <div className="p-6 rounded-2xl bg-white border border-stone-200/90 shadow-xs hover:shadow-md transition-all flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-[#2B5B41] border border-emerald-100 flex items-center justify-center mb-4">
              <Search className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-stone-900 font-heading text-base mb-1.5">
              Find Doctors
            </h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              Search healthcare professionals by name and specialization.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="p-6 rounded-2xl bg-white border border-stone-200/90 shadow-xs hover:shadow-md transition-all flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-[#2B5B41] border border-emerald-100 flex items-center justify-center mb-4">
              <CalendarCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-stone-900 font-heading text-base mb-1.5">
              Easy Appointment Booking
            </h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              View available time slots and book consultations conveniently.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="p-6 rounded-2xl bg-white border border-stone-200/90 shadow-xs hover:shadow-md transition-all flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-[#2B5B41] border border-emerald-100 flex items-center justify-center mb-4">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-stone-900 font-heading text-base mb-1.5">
              Patient Dashboard
            </h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              View upcoming appointments, appointment history, and consultation details.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="p-6 rounded-2xl bg-white border border-stone-200/90 shadow-xs hover:shadow-md transition-all flex flex-col">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-[#2B5B41] border border-emerald-100 flex items-center justify-center mb-4">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-stone-900 font-heading text-base mb-1.5">
              Digital Prescriptions
            </h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              Access prescriptions issued by your doctor.
            </p>
          </div>
        </div>
      </section>

      {/* 4. DOCTOR REGISTRATION BANNER */}
      <section id="for-doctors" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 scroll-mt-24">
        <div className="bg-[#EBF3ED] border border-[#D1E2D6] rounded-3xl p-6 sm:p-10 lg:p-12 relative overflow-hidden">
          <div className="max-w-2xl">
            <h2 className="text-2xl sm:text-3xl font-bold font-heading text-stone-900 mb-3 leading-tight">
              Are You a Healthcare Professional?
            </h2>
            <p className="text-stone-600 text-sm sm:text-base leading-relaxed mb-6">
              Join Amrutam, submit your professional credentials, and connect with patients after verification.
            </p>

            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <Link
                to="/register?role=doctor"
                className="w-full sm:w-auto text-center px-6 py-3 rounded-xl bg-[#2B5B41] hover:bg-[#224834] text-white font-semibold shadow-xs transition-colors text-sm"
              >
                Register as a Doctor
              </Link>
              <span className="text-xs text-stone-500">
                • Verified credentials required before clinical dashboard access
              </span>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
};
