import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-[#1C3E2D] text-stone-300 pt-12 pb-8 border-t border-emerald-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          
          {/* Brand & Description */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-800 flex items-center justify-center text-amber-300">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="font-heading font-bold text-xl text-white tracking-tight">Amrutam</span>
            </div>
            <p className="text-xs sm:text-sm text-stone-300 leading-relaxed max-w-sm">
              A modern telemedicine platform for convenient online consultations and digital healthcare management.
            </p>
          </div>

          {/* Navigation Links */}
          <div>
            <h4 className="font-semibold text-white mb-3 text-xs tracking-wider uppercase">
              Navigation
            </h4>
            <ul className="space-y-2 text-xs sm:text-sm text-stone-300">
              <li>
                <Link to="/" className="hover:text-emerald-300 transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/doctors" className="hover:text-emerald-300 transition-colors">
                  Find Doctors
                </Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-emerald-300 transition-colors">
                  Sign In
                </Link>
              </li>
              <li>
                <Link to="/register?role=doctor" className="hover:text-emerald-300 transition-colors">
                  Register as a Doctor
                </Link>
              </li>
            </ul>
          </div>

          {/* Platform Disclaimer */}
          <div>
            <h4 className="font-semibold text-white mb-3 text-xs tracking-wider uppercase">
              Platform Notice
            </h4>
            <p className="text-xs text-stone-400 leading-relaxed">
              This is a demonstration platform. Doctor profiles and medical information may contain synthetic data. In a medical emergency, seek immediate medical assistance.
            </p>
          </div>

        </div>

        <div className="pt-6 border-t border-emerald-900/60 flex flex-col sm:flex-row items-center justify-between text-xs text-stone-400 gap-3 text-center sm:text-left">
          <div>
            &copy; 2026 Amrutam Telemedicine. All rights reserved.
          </div>
          <div className="text-stone-400 text-xs">
            Ayurvedic Telemedicine Platform
          </div>
        </div>
      </div>
    </footer>
  );
};

