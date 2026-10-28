import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Sparkles,
  Calendar,
  FileText,
  User,
  LogOut,
  Menu,
  X,
  Activity,
  Shield,
  Stethoscope,
  ChevronDown
} from 'lucide-react';

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-stone-200/90 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-[#2B5B41] flex items-center justify-center text-white shadow-sm group-hover:bg-[#224834] transition-colors">
              <Sparkles className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <span className="font-heading font-bold text-2xl tracking-tight text-[#1C3E2D]">
                Amrutam
              </span>
              <span className="block text-[10px] tracking-widest font-semibold uppercase text-stone-500">
                Ayurvedic Telemedicine
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1.5">
            <Link
              to="/"
              className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                isActive('/')
                  ? 'bg-emerald-50 text-[#2B5B41] font-semibold'
                  : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
              }`}
            >
              Home
            </Link>

            <Link
              to="/doctors"
              className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                isActive('/doctors')
                  ? 'bg-emerald-50 text-[#2B5B41] font-semibold'
                  : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
              }`}
            >
              Find Doctors
            </Link>


            {isAuthenticated && user?.role === 'PATIENT' && (
              <>
                <div className="h-4 w-px bg-stone-300 mx-1" />
                <Link
                  to="/patient/appointments"
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/patient/appointments')
                      ? 'bg-[#2B5B41]/10 text-[#2B5B41] font-semibold'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100/70'
                  }`}
                >
                  Appointments
                </Link>
                <Link
                  to="/patient/prescriptions"
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/patient/prescriptions')
                      ? 'bg-[#2B5B41]/10 text-[#2B5B41] font-semibold'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100/70'
                  }`}
                >
                  Prescriptions
                </Link>
              </>
            )}

            {isAuthenticated && user?.role === 'DOCTOR' && (
              <>
                <div className="h-4 w-px bg-stone-300 mx-1" />
                <Link
                  to="/doctor/dashboard"
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/doctor/dashboard')
                      ? 'bg-[#2B5B41]/10 text-[#2B5B41] font-semibold'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100/70'
                  }`}
                >
                  Doctor Workspace
                </Link>
                <Link
                  to="/doctor/availability"
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/doctor/availability')
                      ? 'bg-[#2B5B41]/10 text-[#2B5B41] font-semibold'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100/70'
                  }`}
                >
                  Schedule Slots
                </Link>
              </>
            )}

            {isAuthenticated && user?.role === 'ADMIN' && (
              <>
                <div className="h-4 w-px bg-stone-300 mx-1" />
                <Link
                  to="/admin/dashboard"
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/admin/dashboard')
                      ? 'bg-[#2B5B41]/10 text-[#2B5B41] font-semibold'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100/70'
                  }`}
                >
                  Admin Dashboard
                </Link>
                <Link
                  to="/admin/audit-logs"
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/admin/audit-logs')
                      ? 'bg-[#2B5B41]/10 text-[#2B5B41] font-semibold'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100/70'
                  }`}
                >
                  Audit Logs
                </Link>
              </>
            )}
          </nav>

          {/* User Profile / Auth Actions */}
          <div className="hidden lg:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-semibold text-stone-900">{user.full_name}</div>
                  <div className="flex items-center justify-end gap-1">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      user.role === 'ADMIN'
                        ? 'bg-purple-100 text-purple-700'
                        : user.role === 'DOCTOR'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {user.role}
                    </span>
                  </div>
                </div>

                <Link
                  to="/profile"
                  className="w-10 h-10 rounded-xl bg-stone-200/80 hover:bg-stone-300/80 flex items-center justify-center text-stone-700 transition-colors"
                  title="Profile Settings"
                >
                  <User className="w-5 h-5" />
                </Link>

                <button
                  onClick={handleLogout}
                  className="w-10 h-10 rounded-xl bg-stone-100 hover:bg-rose-50 text-stone-600 hover:text-rose-600 flex items-center justify-center transition-colors"
                  title="Log out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-semibold text-stone-700 hover:text-[#2B5B41] transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/doctors"
                  className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-[#2B5B41] hover:bg-[#224834] shadow-sm transition-all"
                >
                  Book Consultation
                </Link>
              </div>
            )}
          </div>

          {/* Mobile hamburger */}
          <div className="lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
              className="p-2.5 rounded-xl text-stone-600 hover:bg-stone-100 focus:outline-none focus:ring-2 focus:ring-[#2B5B41]"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white border-b border-stone-200 px-4 pt-3 pb-6 space-y-1.5 max-h-[calc(100vh-5rem)] overflow-y-auto">
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
          >
            Home
          </Link>
          <Link
            to="/doctors"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
          >
            Find Doctors
          </Link>
          {isAuthenticated ? (
            <>
              {user.role === 'PATIENT' && (
                <>
                  <Link
                    to="/patient/appointments"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
                  >
                    My Appointments
                  </Link>
                  <Link
                    to="/patient/prescriptions"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
                  >
                    Prescriptions
                  </Link>
                </>
              )}
              {user.role === 'DOCTOR' && (
                <>
                  <Link
                    to="/doctor/dashboard"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
                  >
                    Doctor Workspace
                  </Link>
                  <Link
                    to="/doctor/availability"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
                  >
                    Schedule Slots
                  </Link>
                </>
              )}
              {user.role === 'ADMIN' && (
                <>
                  <Link
                    to="/admin/dashboard"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
                  >
                    Admin Analytics
                  </Link>
                  <Link
                    to="/admin/audit-logs"
                    onClick={() => setMobileMenuOpen(false)}
                    className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
                  >
                    Audit Logs
                  </Link>
                </>
              )}
              <Link
                to="/profile"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-stone-700 hover:bg-stone-50"
              >
                Profile Settings & MFA
              </Link>
              <div className="pt-4 border-t border-stone-100 flex items-center justify-between">
                <Link
                  to="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block min-w-0 pr-2"
                >
                  <div className="font-semibold text-stone-900 truncate">{user.full_name}</div>
                  <div className="text-xs text-stone-500 truncate">{user.email} ({user.role})</div>
                </Link>
                <button
                  onClick={() => { setMobileMenuOpen(false); handleLogout(); }}
                  className="px-3 py-1.5 text-xs font-semibold text-rose-600 bg-rose-50 rounded-lg flex-shrink-0 hover:bg-rose-100 transition-colors"
                >
                  Logout
                </button>
              </div>
            </>
          ) : (
            <div className="pt-4 border-t border-stone-100 flex flex-col gap-2">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center py-2 text-stone-700 font-medium"
              >
                Sign In
              </Link>
              <Link
                to="/doctors"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center py-2.5 rounded-xl bg-[#2B5B41] hover:bg-[#224834] text-white font-medium shadow-sm transition-colors"
              >
                Book Consultation
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
