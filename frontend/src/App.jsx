import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './layouts/AppLayout';
import { ProtectedRoute } from './components/ProtectedRoute';

// Pages
import { Home } from './pages/Home';
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';
import { DoctorsDirectory } from './pages/patient/DoctorsDirectory';
import { PatientAppointments } from './pages/patient/PatientAppointments';
import { PatientPrescriptions } from './pages/patient/PatientPrescriptions';
import { DoctorDashboard } from './pages/doctor/DoctorDashboard';
import { DoctorAvailabilityManager } from './pages/doctor/DoctorAvailabilityManager';
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminAuditLogs } from './pages/admin/AdminAuditLogs';
import { UserProfile } from './pages/UserProfile';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            {/* Public Routes */}
            <Route index element={<Home />} />
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
            <Route path="doctors" element={<DoctorsDirectory />} />

            {/* Patient Routes */}
            <Route
              path="patient/appointments"
              element={
                <ProtectedRoute allowedRoles={['PATIENT']}>
                  <PatientAppointments />
                </ProtectedRoute>
              }
            />
            <Route
              path="patient/prescriptions"
              element={
                <ProtectedRoute allowedRoles={['PATIENT']}>
                  <PatientPrescriptions />
                </ProtectedRoute>
              }
            />

            {/* Doctor Routes */}
            <Route
              path="doctor/dashboard"
              element={
                <ProtectedRoute allowedRoles={['DOCTOR']}>
                  <DoctorDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="doctor/availability"
              element={
                <ProtectedRoute allowedRoles={['DOCTOR']}>
                  <DoctorAvailabilityManager />
                </ProtectedRoute>
              }
            />

            {/* Admin Routes */}
            <Route
              path="admin/dashboard"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/audit-logs"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <AdminAuditLogs />
                </ProtectedRoute>
              }
            />

            {/* Profile Route for Authenticated Users */}
            <Route
              path="profile"
              element={
                <ProtectedRoute>
                  <UserProfile />
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
