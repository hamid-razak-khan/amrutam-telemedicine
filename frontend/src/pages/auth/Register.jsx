import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { register, registerDoctor } from '../../api/auth';
import { Sparkles, User, Mail, Phone, Lock, AlertCircle, CheckCircle2, Loader2, ArrowRight, Stethoscope, Award, FileText } from 'lucide-react';

export const Register = () => {
  const [searchParams] = useSearchParams();
  const initialRole = searchParams.get('role')?.toUpperCase() === 'DOCTOR' ? 'DOCTOR' : 'PATIENT';
  const [roleType, setRoleType] = useState(initialRole);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    password: '',
    password_confirm: '',
    // Doctor specific fields
    specialization: 'General Physician',
    credentials: 'MBBS, MD',
    license_number: '',
    years_of_experience: 5,
    consultation_fee: 600,
    biography: '',
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [doctorSuccessMessage, setDoctorSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.password_confirm) {
      setError('Password and confirmation password do not match.');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must contain at least 8 characters.');
      return;
    }

    if (roleType === 'DOCTOR' && !formData.license_number.trim()) {
      setError('Medical license/registration number is required for doctor applicants.');
      return;
    }

    setLoading(true);

    try {
      if (roleType === 'DOCTOR') {
        const res = await registerDoctor({
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          phone_number: formData.phone_number,
          password: formData.password,
          password_confirm: formData.password_confirm,
          license_number: formData.license_number,
          credentials: formData.credentials,
          specialization: formData.specialization,
          years_of_experience: Number(formData.years_of_experience),
          consultation_fee: Number(formData.consultation_fee),
          biography: formData.biography,
        });
        setDoctorSuccessMessage(res.message || 'Doctor registration submitted successfully. Your account is awaiting administrator approval.');
        setSuccess(true);
      } else {
        await register({
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          phone_number: formData.phone_number,
          password: formData.password,
          password_confirm: formData.password_confirm,
        });
        setDoctorSuccessMessage('');
        setSuccess(true);
      }
    } catch (err) {
      const errData = err.response?.data?.error?.details || err.response?.data?.error?.message || err.response?.data?.email || err.message;
      if (typeof errData === 'object') {
        const firstErr = Object.values(errData)[0];
        setError(Array.isArray(firstErr) ? firstErr[0] : String(firstErr));
      } else {
        setError(String(errData));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex flex-col justify-center py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-2xl herbal-gradient flex items-center justify-center text-white mx-auto shadow-md mb-4">
          <Sparkles className="w-6 h-6 text-amber-300" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold font-heading text-stone-900 tracking-tight">
          {roleType === 'DOCTOR' ? 'Doctor Application' : 'Create Patient Profile'}
        </h2>
        <p className="mt-2 text-xs sm:text-sm text-stone-600">
          {roleType === 'DOCTOR'
            ? 'Apply to practice on Amrutam as a verified Ayurvedic specialist (subject to admin approval)'
            : 'Book verified telemedicine sessions with authenticated Ayurvedic practitioners'}
        </p>

        {/* Role Toggle Selector */}
        {!success && (
          <div className="mt-6 inline-flex max-w-full p-1 bg-stone-100 rounded-xl border border-stone-200">
            <button
              type="button"
              onClick={() => { setRoleType('PATIENT'); setError(''); }}
              className={`px-3 sm:px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 sm:gap-2 ${
                roleType === 'PATIENT' ? 'bg-white text-[#2B5B41] shadow-sm' : 'text-stone-600 hover:text-stone-900'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>Patient Account</span>
            </button>
            <button
              type="button"
              onClick={() => { setRoleType('DOCTOR'); setError(''); }}
              className={`px-3 sm:px-4 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 sm:gap-2 ${
                roleType === 'DOCTOR' ? 'bg-white text-[#2B5B41] shadow-sm' : 'text-stone-600 hover:text-stone-900'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Doctor Practitioner</span>
            </button>
          </div>
        )}
      </div>

      <div className={`mt-6 sm:mx-auto sm:w-full ${roleType === 'DOCTOR' ? 'sm:max-w-xl' : 'sm:max-w-md'}`}>
        <div className="bg-white py-6 sm:py-8 px-4 sm:px-10 shadow-sm border border-stone-200/90 rounded-2xl">
          
          {success ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 bg-emerald-100 text-emerald-800 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold font-heading text-stone-900">
                {roleType === 'DOCTOR' ? 'Application Submitted!' : 'Registration Successful!'}
              </h3>
              <p className="text-sm text-stone-600 max-w-sm mx-auto leading-relaxed">
                {roleType === 'DOCTOR'
                  ? doctorSuccessMessage || 'Your doctor registration request has been submitted. A platform administrator will review your medical credentials before approving account access.'
                  : 'Your patient profile has been securely created. You may now sign in to view doctor schedules and book your consultation.'}
              </p>
              <div className="pt-4">
                <Link
                  to="/login"
                  className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl herbal-gradient text-white font-semibold text-sm shadow-md"
                >
                  <span>Proceed to Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
                  <div>{error}</div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      name="first_name"
                      required
                      value={formData.first_name}
                      onChange={handleChange}
                      placeholder="Ananya"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      name="last_name"
                      required
                      value={formData.last_name}
                      onChange={handleChange}
                      placeholder="Iyer"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="name@example.com"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleChange}
                    placeholder="+91 98765 43210"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                  />
                </div>

                {/* DOCTOR SPECIFIC INPUT FIELDS */}
                {roleType === 'DOCTOR' && (
                  <div className="pt-3 border-t border-stone-100 space-y-4">
                    <div className="text-xs font-bold uppercase tracking-wider text-[#2B5B41]">
                      Professional Credentials
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                          Medical License Number *
                        </label>
                        <input
                          type="text"
                          name="license_number"
                          required
                          value={formData.license_number}
                          onChange={handleChange}
                          placeholder="e.g. AYUSH-DL-2023-889"
                          className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                          Years of Experience
                        </label>
                        <input
                          type="number"
                          name="years_of_experience"
                          min="0"
                          value={formData.years_of_experience}
                          onChange={handleChange}
                          className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                        Degrees & Qualifications
                      </label>
                      <input
                        type="text"
                        name="credentials"
                        required
                        value={formData.credentials}
                        onChange={handleChange}
                        placeholder="e.g. BAMS, MD (Kayachikitsa)"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                          Specialization
                        </label>
                        <select
                          name="specialization"
                          value={formData.specialization}
                          onChange={handleChange}
                          className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                        >
                          <option value="General Physician">General Physician</option>
                          <option value="Dermatology">Dermatology</option>
                          <option value="Pediatrics">Pediatrics</option>
                          <option value="Cardiology">Cardiology</option>
                          <option value="Kayachikitsa & Panchakarma">Kayachikitsa & Panchakarma</option>
                          <option value="Ayurvedic Dermatology & Hair Care">Ayurvedic Dermatology & Hair Care</option>
                          <option value="Joint Care & Musculoskeletal Disorders">Joint Care & Musculoskeletal</option>
                          <option value="Metabolic Health & Women Wellness">Metabolic & Women Wellness</option>
                          <option value="General Ayurvedic Medicine">General Ayurvedic Medicine</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                          Consultation Fee (INR)
                        </label>
                        <input
                          type="number"
                          name="consultation_fee"
                          min="100"
                          step="50"
                          value={formData.consultation_fee}
                          onChange={handleChange}
                          className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                        Clinical Bio
                      </label>
                      <textarea
                        name="biography"
                        rows={2}
                        value={formData.biography}
                        onChange={handleChange}
                        placeholder="Brief overview of clinical practice and focus areas..."
                        className="w-full px-3.5 py-2 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50 resize-none"
                      />
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                      Password (8+ chars)
                    </label>
                    <input
                      type="password"
                      name="password"
                      required
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="••••••••"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                      Confirm Password
                    </label>
                    <input
                      type="password"
                      name="password_confirm"
                      required
                      value={formData.password_confirm}
                      onChange={handleChange}
                      placeholder="••••••••"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#2B5B41] bg-stone-50/50"
                    />
                  </div>
                </div>

                <div className="pt-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3.5 px-4 rounded-xl herbal-gradient text-white font-semibold text-sm shadow-md shadow-emerald-900/10 hover:opacity-95 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Submitting application...</span>
                      </>
                    ) : (
                      <>
                        <span>{roleType === 'DOCTOR' ? 'Submit Doctor Application' : 'Complete Patient Registration'}</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="mt-6 text-center text-xs text-stone-500">
                Already registered?{' '}
                <Link to="/login" className="font-semibold text-[#2B5B41] hover:underline">
                  Sign in here
                </Link>
              </div>
            </>
          )}

        </div>
      </div>
    </div>
  );
};
