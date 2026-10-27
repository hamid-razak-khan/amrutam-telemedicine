import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Sparkles, Lock, Mail, AlertCircle, Loader2, ArrowRight } from 'lucide-react';

export const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname || null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(email, password);
      if (from) {
        navigate(from, { replace: true });
      } else if (user.role === 'ADMIN') {
        navigate('/admin/dashboard', { replace: true });
      } else if (user.role === 'DOCTOR') {
        navigate('/doctor/dashboard', { replace: true });
      } else {
        navigate('/patient/appointments', { replace: true });
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        'Authentication failed. Please verify your email and password.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoFill = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError('');
  };

  return (
    <div className="min-h-[80vh] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-2xl herbal-gradient flex items-center justify-center text-white mx-auto shadow-md mb-4">
          <Sparkles className="w-6 h-6 text-amber-300" />
        </div>
        <h2 className="text-3xl font-bold font-heading text-stone-900 tracking-tight">
          Welcome to Amrutam
        </h2>
        <p className="mt-2 text-sm text-stone-600">
          Sign in to access your consultations, prescriptions, or clinical workspace
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-stone-200/90 rounded-2xl sm:px-10">
          
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
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
                  <span>Sign In to Platform</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-8 pt-6 border-t border-stone-100">
            <div className="text-xs font-bold uppercase tracking-wider text-stone-400 text-center mb-3">
              Fast Demo Credentials
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoFill('patient1@example.com', 'PatientPassword123!')}
                className="p-2 text-center rounded-lg border border-emerald-200 bg-emerald-50/60 hover:bg-emerald-100/70 text-emerald-900 text-xs font-medium transition-colors"
              >
                Patient
              </button>
              <button
                type="button"
                onClick={() => handleDemoFill('dr.sharma@amrutam.co.in', 'DoctorPassword123!')}
                className="p-2 text-center rounded-lg border border-blue-200 bg-blue-50/60 hover:bg-blue-100/70 text-blue-900 text-xs font-medium transition-colors"
              >
                Doctor
              </button>
              <button
                type="button"
                onClick={() => handleDemoFill('admin@amrutam.co.in', 'AdminPassword123!')}
                className="p-2 text-center rounded-lg border border-purple-200 bg-purple-50/60 hover:bg-purple-100/70 text-purple-900 text-xs font-medium transition-colors"
              >
                Admin
              </button>
            </div>
          </div>

          <div className="mt-6 text-center text-xs text-stone-500">
            New to Amrutam?{' '}
            <Link to="/register" className="font-semibold text-[#2B5B41] hover:underline">
              Create a patient account
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
};
