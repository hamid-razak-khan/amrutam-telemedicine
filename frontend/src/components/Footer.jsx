import React from 'react';
import { Heart, Sparkles, ShieldCheck, Clock, Award } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-[#1C3E2D] text-stone-300 pt-16 pb-12 border-t border-emerald-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-800 flex items-center justify-center text-amber-300">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="font-heading font-bold text-xl text-white tracking-tight">Amrutam</span>
            </div>
            <p className="text-sm text-stone-400 leading-relaxed">
              Pioneering authenticated classical Ayurvedic healthcare and precision telemedicine consultations since 2006.
            </p>
            <div className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Certified AYUSH Medical Practitioners</span>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-4 text-sm tracking-wider uppercase font-sans">
              Clinical Specialities
            </h4>
            <ul className="space-y-2 text-sm text-stone-400">
              <li>Kayachikitsa (Internal Medicine)</li>
              <li>Ayurvedic Dermatology & Scalp</li>
              <li>Panchakarma Detoxification</li>
              <li>Musculoskeletal & Marma Care</li>
              <li>Metabolic & Women's Hormonal Health</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-4 text-sm tracking-wider uppercase font-sans">
              Telemedicine Platform
            </h4>
            <ul className="space-y-2 text-sm text-stone-400">
              <li>Zero Double-Booking Guarantee</li>
              <li>Encrypted Medical Prescriptions</li>
              <li>End-to-End Audit Logs</li>
              <li>Transaction Safe Idempotency</li>
              <li>Interactive Ayurvedic Charts</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-4 text-sm tracking-wider uppercase font-sans">
              Clinical Quality & Compliance
            </h4>
            <p className="text-xs text-stone-400 leading-relaxed mb-3">
              Compliant with the Telemedicine Practice Guidelines issued by the Ministry of AYUSH & National Medical Commission.
            </p>
            <div className="p-3 bg-emerald-950/60 rounded-xl border border-emerald-900/60 text-xs text-amber-200">
              <Clock className="w-3.5 h-3.5 inline mr-1 text-amber-300" />
              Emergency cases must immediately visit the nearest tertiary healthcare facility.
            </div>
          </div>

        </div>

        <div className="pt-8 border-t border-emerald-900/60 flex flex-col sm:flex-row items-center justify-between text-xs text-stone-500 gap-4">
          <div>
            &copy; {new Date().getFullYear()} Amrutam Pharmaceuticals Pvt. Ltd. All rights reserved.
          </div>
          <div className="flex items-center gap-6 text-stone-400">
            <span>Security & Threat Model Verified</span>
            <span>GDPR/DISHA Patient Data Isolation</span>
            <span>REST API v1.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
