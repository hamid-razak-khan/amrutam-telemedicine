import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAnalyticsOverview, getConsultationTrends } from '../../api/analytics';
import {
  Users,
  Stethoscope,
  Activity,
  CreditCard,
  TrendingDown,
  ShieldAlert,
  ArrowUpRight,
  FileSpreadsheet,
  Clock,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

export const AdminDashboard = () => {
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(14);
  const [error, setError] = useState('');

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewData, trendsData] = await Promise.all([
        getAnalyticsOverview(),
        getConsultationTrends(days),
      ]);
      setOverview(overviewData.metrics);
      setTrends(trendsData.trends || []);
    } catch (err) {
      setError('Failed to fetch administrative metrics. Administrator access required.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [days]);

  // Format consultations by status for bar visualization
  const statusData = overview?.consultations?.by_status
    ? Object.entries(overview.consultations.by_status).map(([name, count]) => ({
        status: name,
        count: count,
      }))
    : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100 text-purple-900 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5 text-purple-700" />
            <span>Operational & Clinical Analytics</span>
          </div>
          <h1 className="text-3xl font-bold font-heading text-stone-900 tracking-tight">
            Administrative Platform Overview
          </h1>
          <p className="text-sm text-stone-600 mt-1">
            Real-time telemetry, transaction metrics, and consultation trends across the Amrutam platform
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/admin/audit-logs"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-stone-200 bg-white text-stone-700 hover:bg-stone-50 text-xs font-semibold shadow-sm transition-colors"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-[#2B5B41]" />
            <span>Inspect Audit Logs</span>
          </Link>
          <button
            onClick={fetchDashboardData}
            className="p-2.5 rounded-xl border border-stone-200 bg-white text-stone-600 hover:bg-stone-50 shadow-sm"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-stone-500">
            <span className="text-xs font-bold uppercase tracking-wider">Registered Patients</span>
            <Users className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="text-3xl font-bold font-heading text-stone-900">
            {overview?.users?.total_patients ?? 0}
          </div>
          <div className="text-xs text-stone-500">Active patient profiles on platform</div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-stone-500">
            <span className="text-xs font-bold uppercase tracking-wider">Verified Doctors</span>
            <Stethoscope className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-3xl font-bold font-heading text-stone-900">
            {overview?.users?.active_verified_doctors ?? 0}
          </div>
          <div className="text-xs text-stone-500">Certified AYUSH practitioners</div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-stone-500">
            <span className="text-xs font-bold uppercase tracking-wider">Gross Revenue</span>
            <CreditCard className="w-5 h-5 text-purple-600" />
          </div>
          <div className="text-3xl font-bold font-heading text-stone-900">
            ₹{overview?.financials?.gross_revenue?.toLocaleString() ?? 0}
          </div>
          <div className="text-xs text-stone-500">
            {overview?.financials?.successful_transactions ?? 0} successful payments
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-stone-500">
            <span className="text-xs font-bold uppercase tracking-wider">Cancellation Rate</span>
            <TrendingDown className="w-5 h-5 text-rose-500" />
          </div>
          <div className="text-3xl font-bold font-heading text-stone-900">
            {overview?.consultations?.cancellation_rate_percentage ?? 0}%
          </div>
          <div className="text-xs text-stone-500">
            {overview?.consultations?.total_count ?? 0} total scheduled consultations
          </div>
        </div>
      </div>

      {/* Visual Analytics with Recharts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Daily Consultation Trends (Area Chart) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold font-heading text-stone-900">
                Daily Consultation Trajectory
              </h3>
              <p className="text-xs text-stone-500">Volume trends over the selected time window</p>
            </div>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-1.5 rounded-lg border border-stone-200 text-xs bg-stone-50 text-stone-700"
            >
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
            </select>
          </div>

          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2B5B41" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#2B5B41" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#86efac" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#86efac" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="display_date" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="total" name="Total Scheduled" stroke="#2B5B41" strokeWidth={2} fillOpacity={1} fill="url(#colorTotal)" />
                <Area type="monotone" dataKey="completed" name="Completed" stroke="#16a34a" strokeWidth={2} fillOpacity={1} fill="url(#colorCompleted)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Distribution (Bar Chart) */}
        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold font-heading text-stone-900">
              Consultations by Status
            </h3>
            <p className="text-xs text-stone-500">Aggregate lifecycle distribution</p>
          </div>

          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="status" tick={{ fontSize: 9, fill: '#64748B' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="count" name="Consultations" fill="#2B5B41" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

    </div>
  );
};
