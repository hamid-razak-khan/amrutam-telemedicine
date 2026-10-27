import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2, ShieldAlert } from 'lucide-react';

export const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <Loader2 className="w-8 h-8 text-[#2B5B41] animate-spin" />
        <p className="text-sm text-stone-500 font-medium">Verifying session credentials...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return (
      <div className="max-w-md mx-auto my-16 p-8 bg-white border border-rose-100 rounded-2xl shadow-sm text-center">
        <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-stone-900 mb-2 font-heading">Access Denied</h2>
        <p className="text-sm text-stone-600 mb-6">
          Your account role (<span className="font-semibold">{user.role}</span>) does not have authorization to view this section.
        </p>
        <button
          onClick={() => window.history.back()}
          className="px-5 py-2.5 bg-stone-800 hover:bg-stone-900 text-white text-sm font-medium rounded-xl transition-colors"
        >
          Go Back
        </button>
      </div>
    );
  }

  return children;
};
