import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Sparkles, Lock, Mail, AlertCircle, Loader2, ArrowRight, ShieldCheck, AlertTriangle } from 'lucide-react';

export const Login = () => {
  const { login, verifyMfa } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [doctorNotice, setDoctorNotice] = useState(null);
  const [loading, setLoading] = useState(false);

  // Two-Factor Authentication state
  const [isMfaStep, setIsMfaStep] = useState(false);
  const [mfaToken, setMfaToken] = useState('');
  const [mfaCode, setMfaCode] = useState('');

  const from = location.state?.from?.pathname || null;

  const handleRedirect = (user) => {
    if (from) {
      navigate(from, { replace: true });
    } else if (user.role === 'ADMIN') {
      navigate('/admin/dashboard', { replace: true });
    } else if (user.role === 'DOCTOR') {
      navigate('/doctor/dashboard', { replace: true });
    } else {
      navigate('/patient/appointments', { replace: true });
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setDoctorNotice(null);
    setLoading(true);

    try {
      const result = await login(email, password);

      if (result && result.mfa_required) {
        setMfaToken(result.mfa_token);
        setIsMfaStep(true);
        return;
      }

      handleRedirect(result);
    } catch (err) {
      const errData = err.response?.data || {};
      const errCode = errData.code || errData.error?.code;
      const errMsg = errData.detail || errData.message || errData.error?.message;

      if (errCode === 'DOCTOR_APPROVAL_PENDING' || (errMsg && errMsg.includes('awaiting administrator approval'))) {
        setDoctorNotice({
          type: 'PENDING',
          title: 'Doctor Account Awaiting Administrator Approval',
          message: 'Your registration request has been submitted and is currently being reviewed by an administrator. You will be able to access your clinical dashboard once approved.'
        });
      } else if (errCode === 'DOCTOR_APPROVAL_REJECTED' || (errMsg && errMsg.includes('rejected'))) {
        setDoctorNotice({
          type: 'REJECTED',
          title: 'Doctor Registration Rejected',
          message: errMsg || 'Your doctor application has been declined by the platform administrator.'
        });
      } else {
        setError(errMsg || 'Authentication failed. Please verify your email and password.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMfaSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await verifyMfa(mfaToken, mfaCode);
      handleRedirect(user);
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.response?.data?.message || err.response?.data?.error?.message;
      setError(errMsg || 'Invalid verification or recovery code. Please check your authenticator application.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelMfa = () => {
    setIsMfaStep(false);
    setMfaToken('');
    setMfaCode('');
    setError('');
  };

  return (
    <div className="min-h-[80vh] flex flex-col justify-center py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-2xl herbal-gradient flex items-center justify-center text-white mx-auto shadow-md mb-4">
          {isMfaStep ? <ShieldCheck className="w-6 h-6 text-emerald-200" /> : <Sparkles className="w-6 h-6 text-amber-300" />}
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold font-heading text-stone-900 tracking-tight">
          {isMfaStep ? 'Two-Factor Authentication' : 'Welcome to Amrutam'}
        </h2>
        <p className="mt-2 text-xs sm:text-sm text-stone-600">
          {isMfaStep
            ? `Enter the 6-digit code from your authenticator app to sign in as ${email}`
            : 'Sign in to access your consultations, prescriptions, or clinical workspace'}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-6 sm:py-8 px-4 sm:px-10 shadow-sm border border-stone-200/90 rounded-2xl">
          
          {/* Doctor Approval Notice */}
          {doctorNotice && (
            <div className={`mb-6 p-4 rounded-xl border flex items-start gap-3 text-sm ${
              doctorNotice.type === 'PENDING'
                ? 'bg-amber-50 border-amber-300 text-amber-900'
                : 'bg-rose-50 border-rose-300 text-rose-900'
            }`}>
              <AlertTriangle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                doctorNotice.type === 'PENDING' ? 'text-amber-600' : 'text-rose-600'
              }`} />
              <div>
                <div className="font-semibold text-xs uppercase tracking-wider mb-1">{doctorNotice.title}</div>
                <div className="text-xs leading-relaxed">{doctorNotice.message}</div>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {!isMfaStep ? (
            /* STEP 1: Email + Password */
            <form onSubmit={handlePasswordSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#2B5B41] focus:border-transparent text-sm bg-stone-50/50"
                  />
                  <Mail className="w-4 h-4 text-stone-400 absolute right-3.5 top-3.5" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#2B5B41] focus:border-transparent text-sm bg-stone-50/50"
                  />
                  <Lock className="w-4 h-4 text-stone-400 absolute right-3.5 top-3.5" />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 px-4 rounded-xl herbal-gradient text-white font-semibold text-sm shadow-md shadow-emerald-900/10 hover:opacity-95 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Verifying credentials...</span>
                  </>
                ) : (
                  <>
                    <span>Continue to Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          ) : (
            /* STEP 2: TOTP MFA Verification */
            <form onSubmit={handleMfaSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                  Authenticator Code
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    autoFocus
                    value={mfaCode}
                    onChange={(e) => setMfaCode(e.target.value)}
                    placeholder="Enter 6-digit code or backup key"
                    maxLength={16}
                    className="w-full px-4 py-3 text-center tracking-widest text-lg font-mono rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#2B5B41] focus:border-transparent bg-stone-50/50"
                  />
                </div>
                <p className="mt-2 text-xs text-stone-500 text-center">
                  Open your authenticator app (Google Authenticator, Authy, etc.) to view your 6-digit code
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !mfaCode.trim()}
                className="w-full py-3.5 px-4 rounded-xl herbal-gradient text-white font-semibold text-sm shadow-md shadow-emerald-900/10 hover:opacity-95 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Validating code...</span>
                  </>
                ) : (
                  <>
                    <span>Verify & Access Account</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleCancelMfa}
                className="w-full py-2 text-xs text-stone-500 hover:text-stone-800 transition-colors"
              >
                ← Back to password login
              </button>
            </form>
          )}

          {!isMfaStep && (
            <div className="mt-6 text-center text-xs text-stone-500">
              New to Amrutam?{' '}
              <Link to="/register" className="font-semibold text-[#2B5B41] hover:underline">
                Register as Patient or Practitioner
              </Link>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

