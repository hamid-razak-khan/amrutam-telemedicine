import React, { createContext, useContext, useState, useEffect } from 'react';
import { getCurrentUser, login as apiLogin, logout as apiLogout } from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const initAuth = async () => {
    const token = sessionStorage.getItem('amrutam_access_token');
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const data = await getCurrentUser();
      setUser(data.user);
    } catch (err) {
      sessionStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    initAuth();

    const handleSessionExpired = () => {
      setUser(null);
    };

    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () => window.removeEventListener('auth:session-expired', handleSessionExpired);
  }, []);

  const login = async (email, password) => {
    setIsLoading(true);
    try {
      const data = await apiLogin({ email, password });
      sessionStorage.setItem('amrutam_access_token', data.access);
      sessionStorage.setItem('amrutam_refresh_token', data.refresh);
      setUser(data.user);
      return data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    const refreshToken = sessionStorage.getItem('amrutam_refresh_token');
    try {
      if (refreshToken) {
        await apiLogout(refreshToken);
      }
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      sessionStorage.clear();
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const data = await getCurrentUser();
      setUser(data.user);
    } catch (e) {
      // Ignore
    }
  };

  const value = {
    user,
    role: user?.role || null,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
