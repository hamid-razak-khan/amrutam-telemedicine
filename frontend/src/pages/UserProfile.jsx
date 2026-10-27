import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getUserProfile, updateUserProfile } from '../api/users';
import {
  User,
  Phone,
  Mail,
  Shield,
  Heart,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Save
} from 'lucide-react';

export const UserProfile = () => {
  const { user, refreshUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    patient_profile: {
      date_of_birth: '',
      gender: '',
      blood_group: '',
      emergency_contact_name: '',
      emergency_contact_phone: '',
      medical_history_summary: '',
    },
  });

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await getUserProfile();
        setProfile(data.user);
        setFormData({
          first_name: data.user.first_name || '',
          last_name: data.user.last_name || '',
          phone_number: data.user.phone_number || '',
          patient_profile: {
            date_of_birth: data.user.patient_profile?.date_of_birth || '',
            gender: data.user.patient_profile?.gender || '',
            blood_group: data.user.patient_profile?.blood_group || '',
            emergency_contact_name: data.user.patient_profile?.emergency_contact_name || '',
            emergency_contact_phone: data.user.patient_profile?.emergency_contact_phone || '',
            medical_history_summary: data.user.patient_profile?.medical_history_summary || '',
          },
        });
      } catch (err) {
        setError('Failed to load profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handlePatientProfileChange = (e) => {
    setFormData({
      ...formData,
      patient_profile: {
        ...formData.patient_profile,
        [e.target.name]: e.target.value,
      },
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaveLoading(true);
    setMessage('');
    setError('');

    try {
      await updateUserProfile(formData);
      setMessage('Profile updated successfully.');
      await refreshUser();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to update profile.');
    } finally {
      setSaveLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 text-[#2B5B41] animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      <div>
        <h1 className="text-3xl font-bold font-heading text-stone-900 tracking-tight">
          Account & Clinical Profile
        </h1>
        <p className="text-sm text-stone-600 mt-1">
          Review and update your permitted personal information and emergency medical details
        </p>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center gap-3 text-emerald-900 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600" />
          <div>{message}</div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Core Account Info */}
        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
          <h3 className="text-base font-bold font-heading text-stone-900">
            Personal Credentials
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                First Name
              </label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                Last Name
              </label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                Email (Immutable)
              </label>
              <input
                type="email"
                disabled
                value={profile?.email || ''}
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-100 text-stone-500 cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                Phone Number
              </label>
              <input
                type="text"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
              />
            </div>
          </div>
        </div>

        {/* Patient Profile Details if Patient */}
        {user?.role === 'PATIENT' && (
          <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
            <h3 className="text-base font-bold font-heading text-stone-900">
              Clinical & Emergency Information
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                  Gender
                </label>
                <select
                  name="gender"
                  value={formData.patient_profile.gender}
                  onChange={handlePatientProfileChange}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
                >
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="OTHER">Other</option>
                  <option value="PREFER_NOT_TO_SAY">Prefer not to say</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                  Blood Group
                </label>
                <input
                  type="text"
                  name="blood_group"
                  placeholder="e.g. O+, B+"
                  value={formData.patient_profile.blood_group}
                  onChange={handlePatientProfileChange}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                  Emergency Contact Name
                </label>
                <input
                  type="text"
                  name="emergency_contact_name"
                  value={formData.patient_profile.emergency_contact_name}
                  onChange={handlePatientProfileChange}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1">
                Ayurvedic Medical History & Dietary Constitution (Prakriti Notes)
              </label>
              <textarea
                rows={3}
                name="medical_history_summary"
                value={formData.patient_profile.medical_history_summary}
                onChange={handlePatientProfileChange}
                placeholder="Mention any seasonal allergies, digestive issues, or chronic conditions..."
                className="w-full px-3.5 py-2.5 rounded-xl border border-stone-200 text-xs bg-stone-50/50"
              />
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saveLoading}
            className="px-6 py-3 rounded-xl herbal-gradient text-white text-xs font-semibold shadow-md flex items-center gap-2 hover:opacity-95 disabled:opacity-50"
          >
            {saveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            <span>Save Profile Updates</span>
          </button>
        </div>

      </form>

    </div>
  );
};
