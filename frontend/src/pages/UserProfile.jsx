import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getUserProfile, updateUserProfile } from '../api/users';
import { getMfaStatus, setupMfa, confirmMfa, disableMfa } from '../api/auth';
import {
  User,
  Phone,
  Mail,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Heart,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Save,
  Key,
  QrCode,
  Copy,
  Check,
  Download,
  Lock
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

  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaLoading, setMfaLoading] = useState(true);
  const [mfaSetupData, setMfaSetupData] = useState(null);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaActionLoading, setMfaActionLoading] = useState(false);
  const [mfaMessage, setMfaMessage] = useState('');
  const [mfaError, setMfaError] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState([]);
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [copiedCodes, setCopiedCodes] = useState(false);
  const [showDisableForm, setShowDisableForm] = useState(false);
  const [disableCode, setDisableCode] = useState('');
  const [disablePassword, setDisablePassword] = useState('');

  const fetchMfaStatus = async () => {
    setMfaLoading(true);
    try {
      const data = await getMfaStatus();
      setMfaEnabled(Boolean(data?.mfa_enabled));
    } catch (err) {
      console.error('Failed to fetch MFA status:', err);
    } finally {
      setMfaLoading(false);
    }
  };

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
    fetchMfaStatus();
  }, []);

  const handleStartMfaSetup = async () => {
    setMfaActionLoading(true);
    setMfaError('');
    setMfaMessage('');
    setRecoveryCodes([]);
    try {
      const data = await setupMfa();
      setMfaSetupData(data);
    } catch (err) {
      setMfaError(err.response?.data?.error?.message || 'Failed to initialize MFA setup.');
    } finally {
      setMfaActionLoading(false);
    }
  };

  const handleConfirmMfa = async (e) => {
    e.preventDefault();
    if (!mfaCode || mfaCode.trim().length !== 6) {
      setMfaError('Please enter a valid 6-digit authenticator code.');
      return;
    }
    setMfaActionLoading(true);
    setMfaError('');
    setMfaMessage('');
    try {
      const res = await confirmMfa(mfaCode.trim());
      setMfaEnabled(true);
      setRecoveryCodes(res.recovery_codes || []);
      setMfaMessage('Two-Factor Authentication activated successfully! Please store your recovery codes securely.');
      setMfaSetupData(null);
      setMfaCode('');
      await refreshUser();
    } catch (err) {
      setMfaError(err.response?.data?.error?.message || 'Invalid confirmation code. Please check your authenticator app and try again.');
    } finally {
      setMfaActionLoading(false);
    }
  };

  const handleDisableMfa = async (e) => {
    e.preventDefault();
    if (!disablePassword) {
      setMfaError('Please enter your account password.');
      return;
    }
    if (!disableCode || disableCode.trim().length < 6) {
      setMfaError('Please enter a valid 6-digit TOTP code or recovery code to disable 2FA.');
      return;
    }
    setMfaActionLoading(true);
    setMfaError('');
    setMfaMessage('');
    try {
      await disableMfa({ password: disablePassword, code: disableCode.trim() });
      setMfaEnabled(false);
      setShowDisableForm(false);
      setDisableCode('');
      setDisablePassword('');
      setRecoveryCodes([]);
      setMfaMessage('Two-Factor Authentication has been successfully disabled.');
      await refreshUser();
    } catch (err) {
      setMfaError(err.response?.data?.error?.message || 'Failed to disable 2FA. Please verify your password and code.');
    } finally {
      setMfaActionLoading(false);
    }
  };

  const handleCopySecret = () => {
    if (mfaSetupData?.secret) {
      navigator.clipboard.writeText(mfaSetupData.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2500);
    }
  };

  const handleCopyRecoveryCodes = () => {
    if (recoveryCodes.length > 0) {
      navigator.clipboard.writeText(recoveryCodes.join('\n'));
      setCopiedCodes(true);
      setTimeout(() => setCopiedCodes(false), 2500);
    }
  };

  const handleDownloadRecoveryCodes = () => {
    if (recoveryCodes.length > 0) {
      const element = document.createElement('a');
      const file = new Blob([
        `AMRUTAM TELEMEDICINE - 2FA BACKUP RECOVERY CODES\n` +
        `Account: ${profile?.email || user?.email}\n` +
        `Generated: ${new Date().toISOString()}\n\n` +
        `Keep these codes confidential. Each recovery code can only be used once to log in:\n\n` +
        recoveryCodes.map((c, i) => `${i + 1}. ${c}`).join('\n') +
        `\n`
      ], { type: 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = `amrutam-recovery-codes-${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  };

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
        <div className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
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
          <div className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
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
            className="w-full sm:w-auto px-6 py-3 rounded-xl herbal-gradient text-white text-xs font-semibold shadow-md flex items-center justify-center gap-2 hover:opacity-95 disabled:opacity-50"
          >
            {saveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            <span>Save Profile Updates</span>
          </button>
        </div>

      </form>

      {/* Two-Factor Authentication (MFA) Settings Card */}
      <div className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-100 pb-5">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${mfaEnabled ? 'bg-emerald-50 text-emerald-700' : 'bg-stone-100 text-stone-600'}`}>
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold font-heading text-stone-900">
                Two-Factor Authentication (TOTP MFA)
              </h3>
              <p className="text-xs text-stone-500">
                Enhance account security with a time-based one-time password authenticator app
              </p>
            </div>
          </div>

          <div>
            {mfaLoading ? (
              <div className="flex items-center gap-1.5 text-xs text-stone-400">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Checking status...</span>
              </div>
            ) : mfaEnabled ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
                <Check className="w-3.5 h-3.5" />
                <span>Active & Enforced</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-stone-100 text-stone-700 text-xs font-semibold">
                <span>Not Enabled</span>
              </span>
            )}
          </div>
        </div>

        {mfaMessage && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center gap-3 text-emerald-900 text-xs font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{mfaMessage}</span>
          </div>
        )}

        {mfaError && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-rose-800 text-xs font-medium">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{mfaError}</span>
          </div>
        )}

        {/* Display newly generated backup recovery codes if available */}
        {recoveryCodes.length > 0 && (
          <div className="p-5 rounded-2xl bg-amber-50/80 border border-amber-200 space-y-4">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900">
                  Save Your Emergency Recovery Codes
                </h4>
                <p className="text-xs text-amber-700 mt-0.5">
                  If you lose access to your authenticator app, each of these 8 codes can be used once as an emergency backup. Store them in a secure password manager or offline location. They will not be displayed again.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-white/90 p-3.5 rounded-xl border border-amber-200/60 font-mono text-xs text-stone-800 text-center select-all">
              {recoveryCodes.map((code, idx) => (
                <div key={idx} className="p-2 bg-stone-50 rounded-lg border border-stone-200/60 tracking-wider font-semibold">
                  {code}
                </div>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <button
                type="button"
                onClick={handleCopyRecoveryCodes}
                className="px-4 py-2 rounded-xl bg-white border border-amber-300 text-amber-900 text-xs font-semibold hover:bg-amber-100/50 flex items-center gap-1.5 shadow-sm"
              >
                {copiedCodes ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedCodes ? 'Copied to Clipboard' : 'Copy All Codes'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadRecoveryCodes}
                className="px-4 py-2 rounded-xl bg-amber-600 text-white text-xs font-semibold hover:bg-amber-700 flex items-center gap-1.5 shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Backup (.txt)</span>
              </button>
            </div>
          </div>
        )}

        {/* If MFA is NOT active and setup hasn't started */}
        {!mfaEnabled && !mfaSetupData && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-stone-50 border border-stone-200/80">
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-800">
                Setup Authenticator Application
              </h4>
              <p className="text-xs text-stone-600">
                Works with Google Authenticator, Microsoft Authenticator, Apple Passwords, 1Password, or Authy.
              </p>
            </div>
            <button
              type="button"
              onClick={handleStartMfaSetup}
              disabled={mfaActionLoading}
              className="px-5 py-2.5 rounded-xl herbal-gradient text-white text-xs font-semibold shadow hover:opacity-95 disabled:opacity-50 flex items-center gap-2 whitespace-nowrap self-start sm:self-auto"
            >
              {mfaActionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Key className="w-3.5 h-3.5" />}
              <span>Enable 2FA</span>
            </button>
          </div>
        )}

        {/* If MFA Setup is in progress (QR Code and Confirmation) */}
        {!mfaEnabled && mfaSetupData && (
          <div className="p-4 sm:p-6 rounded-2xl bg-stone-50 border border-stone-200 space-y-6">
            <div className="border-b border-stone-200 pb-3 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-stone-900">
                  Step 1: Scan QR Code with Authenticator App
                </h4>
                <p className="text-xs text-stone-500 mt-0.5">
                  Open your authenticator app (Google Authenticator, Authy, etc.) and scan the QR code below.
                </p>
              </div>
              <button
                type="button"
                onClick={() => { setMfaSetupData(null); setMfaError(''); }}
                className="text-xs text-stone-500 hover:text-stone-800 font-semibold"
              >
                Cancel
              </button>
            </div>

            <div className="flex flex-col md:flex-row items-center gap-6">
              {mfaSetupData.qr_code && (
                <div className="p-3 bg-white rounded-2xl border border-stone-200 shadow-sm flex-shrink-0 mx-auto md:mx-0">
                  <img
                    src={mfaSetupData.qr_code}
                    alt="Amrutam TOTP QR Code"
                    className="w-40 sm:w-48 h-40 sm:h-48 object-contain"
                  />
                </div>
              )}

              <div className="space-y-4 flex-1 w-full">
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-stone-600 uppercase tracking-wider block">
                    Can't scan? Enter key manually:
                  </span>
                  <div className="flex items-center gap-2">
                    <code className="px-3 py-2 rounded-xl bg-white border border-stone-200 text-xs font-mono font-bold tracking-widest text-[#2B5B41] flex-1 break-all">
                      {mfaSetupData.secret}
                    </code>
                    <button
                      type="button"
                      onClick={handleCopySecret}
                      className="p-2 rounded-xl bg-white border border-stone-200 hover:bg-stone-100 text-stone-600 shadow-sm"
                      title="Copy Key"
                    >
                      {copiedSecret ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <form onSubmit={handleConfirmMfa} className="space-y-3 pt-2">
                  <label className="block text-xs font-bold text-stone-800 uppercase tracking-wider">
                    Step 2: Enter 6-digit Code from Authenticator
                  </label>
                  <div className="flex flex-wrap sm:flex-nowrap gap-3">
                    <input
                      type="text"
                      maxLength={6}
                      value={mfaCode}
                      onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="000000"
                      className="w-full sm:w-36 px-3.5 py-2.5 rounded-xl border border-stone-200 text-center font-mono text-base font-bold tracking-widest bg-white"
                      required
                    />
                    <button
                      type="submit"
                      disabled={mfaActionLoading || mfaCode.length !== 6}
                      className="w-full sm:w-auto px-5 py-2.5 rounded-xl herbal-gradient text-white text-xs font-semibold shadow hover:opacity-95 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {mfaActionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                      <span>Verify & Activate</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* If MFA is already active */}
        {mfaEnabled && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-stone-50 border border-stone-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Lock className="w-4 h-4 text-[#2B5B41] flex-shrink-0" />
                <p className="text-xs text-stone-700">
                  Your account requires a 6-digit TOTP authenticator code or single-use recovery code on every login attempt.
                </p>
              </div>

              {!showDisableForm && (
                <button
                  type="button"
                  onClick={() => { setShowDisableForm(true); setMfaError(''); setMfaMessage(''); }}
                  className="px-4 py-2 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs font-semibold hover:bg-rose-100 flex-shrink-0"
                >
                  Disable 2FA
                </button>
              )}
            </div>

            {showDisableForm && (
              <div className="p-5 rounded-2xl bg-rose-50/60 border border-rose-200 space-y-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h5 className="text-xs font-bold text-rose-900 uppercase tracking-wider">
                      Confirm Deactivation of Two-Factor Authentication
                    </h5>
                    <p className="text-xs text-rose-700 mt-0.5">
                      Enter a valid 6-digit code from your authenticator app or an unused recovery code to confirm disabling.
                    </p>
                  </div>
                </div>

                <form onSubmit={handleDisableMfa} className="space-y-3">
                  <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-3">
                    <input
                      type="password"
                      value={disablePassword}
                      onChange={(e) => setDisablePassword(e.target.value)}
                      placeholder="Account password"
                      className="w-full sm:w-56 px-3.5 py-2.5 rounded-xl border border-rose-200 text-xs bg-white text-stone-900 focus:outline-none focus:ring-2 focus:ring-rose-500"
                      required
                    />
                    <input
                      type="text"
                      value={disableCode}
                      onChange={(e) => setDisableCode(e.target.value)}
                      placeholder="6-digit TOTP or recovery code"
                      className="w-full sm:w-56 px-3.5 py-2.5 rounded-xl border border-rose-200 text-xs bg-white text-stone-900 focus:outline-none focus:ring-2 focus:ring-rose-500"
                      required
                    />
                    <button
                      type="submit"
                      disabled={mfaActionLoading}
                      className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {mfaActionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                      <span>Confirm Disable</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => { setShowDisableForm(false); setDisableCode(''); setDisablePassword(''); }}
                      className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-stone-200 bg-white text-stone-600 text-xs font-semibold hover:bg-stone-50"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}

      </div>

    </div>
  );
};
