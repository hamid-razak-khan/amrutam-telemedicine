import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAnalyticsOverview, getConsultationTrends } from '../../api/analytics';
import {
  getAdminDoctorApplications,
  approveDoctor,
  rejectDoctor,
  removeDoctor
} from '../../api/doctors';
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
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Check,
  X,
  Search,
  UserCheck,
  UserX,
  UserMinus,
  Calendar,
  Filter,
  BadgeCheck
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
  const [activeTab, setActiveTab] = useState('analytics'); // 'analytics' | 'doctors'
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(14);
  const [error, setError] = useState('');

  // Doctor applications state
  const [doctorApplications, setDoctorApplications] = useState([]);
  const [doctorFilter, setDoctorFilter] = useState('PENDING'); // 'PENDING' | 'APPROVED' | 'REMOVED' | 'REJECTED' | ''
  const [doctorLoading, setDoctorLoading] = useState(false);
  const [doctorActionLoading, setDoctorActionLoading] = useState(false);
  const [doctorMessage, setDoctorMessage] = useState('');
  const [doctorError, setDoctorError] = useState('');
  const [rejectModalDoctor, setRejectModalDoctor] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [removeModalDoctor, setRemoveModalDoctor] = useState(null);
  const [removalReason, setRemovalReason] = useState('No longer working with the organization');
  const [pendingCount, setPendingCount] = useState(0);
  const [counts, setCounts] = useState({ pending: 0, approved: 0, removed: 0, rejected: 0, total: 0 });

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return String(dateStr);
    }
  };

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [overviewRes, trendsRes] = await Promise.allSettled([
        getAnalyticsOverview(),
        getConsultationTrends(days),
      ]);

      if (overviewRes.status === 'fulfilled') {
        setOverview(overviewRes.value.metrics);
      }
      if (trendsRes.status === 'fulfilled') {
        setTrends(trendsRes.value.trends || []);
      }

      if (overviewRes.status === 'rejected' && trendsRes.status === 'rejected') {
        const err = overviewRes.reason;
        const msg = err.response?.data?.error?.message 
          || (err.response?.status === 403 ? 'Administrator access required.' : 'Failed to fetch administrative metrics.');
        setError(msg);
      } else if (overviewRes.status === 'rejected') {
        const err = overviewRes.reason;
        setError(err.response?.data?.error?.message || 'Failed to fetch overview metrics.');
      } else if (trendsRes.status === 'rejected') {
        const err = trendsRes.reason;
        setError(err.response?.data?.error?.message || 'Failed to load consultation trends.');
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to fetch administrative metrics.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDoctorApplications = async (filter = doctorFilter) => {
    setDoctorLoading(true);
    setDoctorError('');
    try {
      const [filteredData, allData] = await Promise.all([
        getAdminDoctorApplications(filter || null),
        getAdminDoctorApplications(null)
      ]);

      setDoctorApplications(filteredData.doctors || []);

      const allDocs = allData.doctors || [];
      const pending = allDocs.filter(d => d.verification_status === 'PENDING').length;
      const approved = allDocs.filter(d => d.verification_status === 'APPROVED' || d.verification_status === 'VERIFIED').length;
      const removed = allDocs.filter(d => d.verification_status === 'REMOVED').length;
      const rejected = allDocs.filter(d => d.verification_status === 'REJECTED').length;

      setCounts({ pending, approved, removed, rejected, total: allDocs.length });
      setPendingCount(pending);
    } catch (err) {
      setDoctorError(err.response?.data?.error?.message || 'Failed to load doctor applications.');
    } finally {
      setDoctorLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchDoctorApplications('PENDING');
  }, [days]);

  const handleFilterChange = (newFilter) => {
    setDoctorFilter(newFilter);
    fetchDoctorApplications(newFilter);
  };

  const handleApproveDoctor = async (doctorId, doctorName) => {
    setDoctorActionLoading(true);
    setDoctorMessage('');
    setDoctorError('');
    try {
      await approveDoctor(doctorId);
      setDoctorMessage(`Doctor ${doctorName || ''} approved/restored successfully. They may now sign in and publish availability slots.`);
      await fetchDoctorApplications(doctorFilter);
      await fetchDashboardData();
    } catch (err) {
      setDoctorError(err.response?.data?.error?.message || 'Failed to approve doctor.');
    } finally {
      setDoctorActionLoading(false);
    }
  };

  const handleOpenRejectModal = (doctor) => {
    setRejectModalDoctor(doctor);
    setRejectionReason('Registration credentials or medical license could not be verified.');
    setDoctorError('');
    setDoctorMessage('');
  };

  const handleConfirmReject = async (e) => {
    e.preventDefault();
    if (!rejectModalDoctor) return;
    setDoctorActionLoading(true);
    setDoctorError('');
    setDoctorMessage('');
    try {
      await rejectDoctor(rejectModalDoctor.id, rejectionReason);
      setDoctorMessage(`Application for Dr. ${rejectModalDoctor.user?.first_name || ''} was rejected.`);
      setRejectModalDoctor(null);
      await fetchDoctorApplications(doctorFilter);
      await fetchDashboardData();
    } catch (err) {
      setDoctorError(err.response?.data?.error?.message || 'Failed to reject doctor.');
    } finally {
      setDoctorActionLoading(false);
    }
  };

  const handleOpenRemoveModal = (doctor) => {
    setRemoveModalDoctor(doctor);
    setRemovalReason('Doctor has completed engagement / no longer working with the organization.');
    setDoctorError('');
    setDoctorMessage('');
  };

  const handleConfirmRemove = async (e) => {
    e.preventDefault();
    if (!removeModalDoctor) return;
    setDoctorActionLoading(true);
    setDoctorError('');
    setDoctorMessage('');
    try {
      await removeDoctor(removeModalDoctor.id, removalReason);
      setDoctorMessage(`Dr. ${removeModalDoctor.user?.first_name || ''} ${removeModalDoctor.user?.last_name || ''} has been removed from active practice.`);
      setRemoveModalDoctor(null);
      await fetchDoctorApplications(doctorFilter);
      await fetchDashboardData();
    } catch (err) {
      setDoctorError(err.response?.data?.error?.message || 'Failed to remove doctor.');
    } finally {
      setDoctorActionLoading(false);
    }
  };


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

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-stone-200 pb-2 overflow-x-auto flex-nowrap sm:flex-wrap">
        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeTab === 'analytics'
              ? 'bg-[#2B5B41] text-white shadow-sm'
              : 'text-stone-600 hover:bg-stone-100'
          }`}
        >
          <Activity className="w-4 h-4 flex-shrink-0" />
          <span>Platform Telemetry & Analytics</span>
        </button>

        <button
          onClick={() => { setActiveTab('doctors'); fetchDoctorApplications(doctorFilter); }}
          className={`flex items-center gap-2 px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeTab === 'doctors'
              ? 'bg-[#2B5B41] text-white shadow-sm'
              : 'text-stone-600 hover:bg-stone-100'
          }`}
        >
          <Stethoscope className="w-4 h-4 flex-shrink-0" />
          <span>Doctor Registrations & Approvals</span>
          {pendingCount > 0 && (
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
              activeTab === 'doctors' ? 'bg-amber-400 text-stone-900' : 'bg-amber-100 text-amber-900'
            }`}>
              {pendingCount} Pending
            </span>
          )}
        </button>
      </div>

      {doctorMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center gap-3 text-emerald-900 text-xs font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{doctorMessage}</span>
        </div>
      )}

      {doctorError && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-rose-800 text-xs font-medium">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{doctorError}</span>
        </div>
      )}

      {/* Tab 1: Operational Analytics */}
      {activeTab === 'analytics' && (
        <div className="space-y-8">
          {/* Primary KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 sm:gap-6">
            <div className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-stone-500">
                <span className="text-xs font-bold uppercase tracking-wider">Registered Patients</span>
                <Users className="w-5 h-5 text-emerald-600" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-heading text-stone-900">
                {overview?.users?.total_patients ?? 0}
              </div>
              <div className="text-xs text-stone-500">Active patient profiles on platform</div>
            </div>

            <div className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-stone-500">
                <span className="text-xs font-bold uppercase tracking-wider">Verified Doctors</span>
                <Stethoscope className="w-5 h-5 text-blue-600" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-heading text-stone-900">
                {overview?.users?.active_verified_doctors ?? 0}
              </div>
              <div className="text-xs text-stone-500">Certified AYUSH practitioners</div>
            </div>

            <div className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-stone-500">
                <span className="text-xs font-bold uppercase tracking-wider">Gross Revenue</span>
                <CreditCard className="w-5 h-5 text-purple-600" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-heading text-stone-900">
                ₹{overview?.financials?.gross_revenue?.toLocaleString() ?? 0}
              </div>
              <div className="text-xs text-stone-500">
                {overview?.financials?.successful_transactions ?? 0} successful payments
              </div>
            </div>

            <div className="bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-stone-500">
                <span className="text-xs font-bold uppercase tracking-wider">Cancellation Rate</span>
                <TrendingDown className="w-5 h-5 text-rose-500" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold font-heading text-stone-900">
                {overview?.consultations?.cancellation_rate_percentage ?? 0}%
              </div>
              <div className="text-xs text-stone-500">
                {overview?.consultations?.total_count ?? 0} total scheduled consultations
              </div>
            </div>
          </div>

          {/* Visual Analytics with Recharts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
            
            {/* Daily Consultation Trends (Area Chart) */}
            <div className="lg:col-span-2 min-w-0 bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-base font-bold font-heading text-stone-900">
                    Daily Consultation Trajectory
                  </h3>
                  <p className="text-xs text-stone-500">Volume trends over the selected time window</p>
                </div>
                <select
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="px-3 py-1.5 rounded-lg border border-stone-200 text-xs bg-stone-50 text-stone-700 self-start sm:self-auto"
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
            <div className="min-w-0 bg-white p-4 sm:p-6 rounded-2xl border border-stone-200 shadow-sm space-y-4">
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
      )}

      {/* Tab 2: Doctor Practitioner Approvals */}
      {activeTab === 'doctors' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 sm:p-5 rounded-2xl border border-stone-200 shadow-sm">
            <div>
              <h3 className="text-base font-bold font-heading text-stone-900">
                AYUSH Practitioner Review & Licensing Verification
              </h3>
              <p className="text-xs text-stone-500 mt-0.5">
                Review submitted practitioner credentials, state medical council licenses, and grant or reject platform access.
              </p>
            </div>

            {/* Filter pills */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
              {[
                { label: 'Pending Review', value: 'PENDING', count: counts.pending, badgeColor: 'bg-amber-100 text-amber-800' },
                { label: 'Approved', value: 'APPROVED', count: counts.approved, badgeColor: 'bg-emerald-100 text-emerald-800' },
                { label: 'Removed Doctors', value: 'REMOVED', count: counts.removed, badgeColor: 'bg-rose-100 text-rose-800' },
                { label: 'Rejected', value: 'REJECTED', count: counts.rejected, badgeColor: 'bg-stone-200 text-stone-700' },
                { label: 'All Practitioners', value: '', count: counts.total, badgeColor: 'bg-stone-200 text-stone-700' },
              ].map((f) => (
                <button
                  key={f.value}
                  onClick={() => handleFilterChange(f.value)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                    doctorFilter === f.value
                      ? 'bg-[#2B5B41] text-white shadow-sm ring-1 ring-[#2B5B41]'
                      : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                  }`}
                >
                  <span>{f.label}</span>
                  {typeof f.count === 'number' && f.count > 0 && (
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                      doctorFilter === f.value
                        ? 'bg-white/20 text-white'
                        : f.badgeColor
                    }`}>
                      {f.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Applications Table */}
          <div className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden">
            {doctorLoading ? (
              <div className="flex items-center justify-center py-16">
                <RefreshCw className="w-6 h-6 text-[#2B5B41] animate-spin" />
              </div>
            ) : doctorApplications.length === 0 ? (
              <div className="text-center py-16 px-4">
                <Stethoscope className="w-12 h-12 text-stone-300 mx-auto mb-3" />
                <h4 className="text-sm font-bold text-stone-800">No practitioners found</h4>
                <p className="text-xs text-stone-500 mt-1">
                  {doctorFilter === 'PENDING'
                    ? 'No doctor registrations are currently awaiting administrative approval.'
                    : doctorFilter === 'REMOVED'
                    ? 'No removed doctors. All organization doctors are currently in good standing.'
                    : 'No practitioner profiles match the selected status filter.'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[840px] text-left text-xs">
                  <thead className="bg-stone-50 text-stone-600 uppercase font-bold text-[10px] tracking-wider border-b border-stone-200">
                    <tr>
                      <th className="py-3.5 px-4">Doctor Practitioner</th>
                      <th className="py-3.5 px-4">License & Credentials</th>
                      <th className="py-3.5 px-4">Specialization / Fee</th>
                      <th className="py-3.5 px-4">Joining & Removal Dates</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {doctorApplications.map((doc) => {
                      const isPending = doc.verification_status === 'PENDING';
                      const isApproved = doc.verification_status === 'APPROVED' || doc.verification_status === 'VERIFIED';
                      const isRemoved = doc.verification_status === 'REMOVED';
                      const isRejected = doc.verification_status === 'REJECTED';

                      return (
                        <tr key={doc.id} className="hover:bg-stone-50/70 transition-colors">
                          <td className="py-4 px-4">
                            <div className="font-bold text-stone-900">
                              Dr. {doc.user?.first_name} {doc.user?.last_name}
                            </div>
                            <div className="text-stone-500 text-[11px]">{doc.user?.email}</div>
                            {doc.user?.phone_number && (
                              <div className="text-stone-400 text-[10px]">{doc.user?.phone_number}</div>
                            )}
                          </td>

                          <td className="py-4 px-4">
                            <div className="font-mono font-semibold text-stone-800">
                              {doc.license_number || 'Not provided'}
                            </div>
                            <div className="text-stone-500 text-[11px]">
                              {doc.credentials || 'AYUSH Practitioner'}
                            </div>
                          </td>

                          <td className="py-4 px-4">
                            <div className="font-medium text-stone-800">{doc.specialization}</div>
                            <div className="text-stone-500 text-[11px] mt-0.5">
                              {doc.years_of_experience || 0} yrs exp. • <span className="font-semibold text-[#2B5B41]">₹{doc.consultation_fee || 0}</span>
                            </div>
                          </td>

                          <td className="py-4 px-4">
                            <div className="space-y-1">
                              <div className="flex items-center gap-1.5 text-stone-700">
                                <span className="text-[10px] uppercase font-bold text-stone-400">Joined:</span>
                                <span className="font-medium text-stone-800">{formatDate(doc.joining_date)}</span>
                              </div>
                              {doc.removed_at ? (
                                <div className="flex items-center gap-1.5 text-rose-700">
                                  <span className="text-[10px] uppercase font-bold text-rose-400">Removed:</span>
                                  <span className="font-semibold text-rose-700">{formatDate(doc.removed_at)}</span>
                                </div>
                              ) : isApproved ? (
                                <div className="text-[10px] text-emerald-600 font-medium flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                  <span>Active with Organization</span>
                                </div>
                              ) : null}
                            </div>
                          </td>

                          <td className="py-4 px-4">
                            {isPending && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-100 text-amber-900 font-semibold text-[11px]">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                                <span>Pending Approval</span>
                              </span>
                            )}
                            {isApproved && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-900 font-semibold text-[11px]">
                                <BadgeCheck className="w-3.5 h-3.5 text-emerald-600" />
                                <span>Approved</span>
                              </span>
                            )}
                            {isRemoved && (
                              <div>
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-800 font-semibold text-[11px]">
                                  <UserMinus className="w-3.5 h-3.5 text-rose-600" />
                                  <span>Removed from Org</span>
                                </span>
                                {doc.removal_reason && (
                                  <p className="text-[10px] text-stone-500 mt-1 max-w-xs truncate" title={doc.removal_reason}>
                                    Reason: {doc.removal_reason}
                                  </p>
                                )}
                              </div>
                            )}
                            {isRejected && (
                              <div>
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-100 text-rose-900 font-semibold text-[11px]">
                                  <XCircle className="w-3.5 h-3.5 text-rose-600" />
                                  <span>Rejected</span>
                                </span>
                                {doc.rejection_reason && (
                                  <p className="text-[10px] text-rose-600 mt-1 max-w-xs truncate" title={doc.rejection_reason}>
                                    Reason: {doc.rejection_reason}
                                  </p>
                                )}
                              </div>
                            )}
                          </td>

                          <td className="py-4 px-4 text-right">
                            {isPending ? (
                              <div className="inline-flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => handleApproveDoctor(doc.id, `Dr. ${doc.user?.first_name} ${doc.user?.last_name}`)}
                                  disabled={doctorActionLoading}
                                  className="px-3 py-1.5 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1 shadow-sm"
                                  title="Approve Practitioner"
                                >
                                  <Check className="w-3.5 h-3.5" />
                                  <span>Approve</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleOpenRejectModal(doc)}
                                  disabled={doctorActionLoading}
                                  className="px-3 py-1.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 font-semibold hover:bg-rose-100 disabled:opacity-50 flex items-center gap-1"
                                  title="Reject Application"
                                >
                                  <X className="w-3.5 h-3.5" />
                                  <span>Reject</span>
                                </button>
                              </div>
                            ) : isApproved ? (
                              <button
                                type="button"
                                onClick={() => handleOpenRemoveModal(doc)}
                                disabled={doctorActionLoading}
                                className="px-3 py-1.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 font-semibold hover:bg-rose-100 disabled:opacity-50 inline-flex items-center gap-1.5 text-xs transition-colors"
                                title="Remove doctor who is no longer working with the organization"
                              >
                                <UserMinus className="w-3.5 h-3.5" />
                                <span>Remove Doctor</span>
                              </button>
                            ) : isRemoved ? (
                              <button
                                type="button"
                                onClick={() => handleApproveDoctor(doc.id, `Dr. ${doc.user?.first_name} ${doc.user?.last_name}`)}
                                disabled={doctorActionLoading}
                                className="px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold hover:bg-emerald-100 disabled:opacity-50 inline-flex items-center gap-1.5 text-xs transition-colors"
                                title="Restore doctor to active practice"
                              >
                                <Check className="w-3.5 h-3.5" />
                                <span>Restore Doctor</span>
                              </button>
                            ) : (
                              <button
                                type="button"
                                onClick={() => handleApproveDoctor(doc.id, `Dr. ${doc.user?.first_name} ${doc.user?.last_name}`)}
                                disabled={doctorActionLoading}
                                className="px-2.5 py-1 rounded-lg text-emerald-700 hover:bg-emerald-50 text-[11px] font-semibold"
                              >
                                Re-approve
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Rejection Modal */}
      {rejectModalDoctor && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-4 sm:p-6 max-h-[90vh] overflow-y-auto shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-stone-100 pb-3">
              <div className="flex items-center gap-2 text-rose-600">
                <UserX className="w-5 h-5" />
                <h4 className="text-base font-bold text-stone-900">
                  Reject Doctor Application
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setRejectModalDoctor(null)}
                className="text-stone-400 hover:text-stone-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-stone-600">
              You are rejecting the practitioner registration for{' '}
              <strong className="text-stone-900">
                Dr. {rejectModalDoctor.user?.first_name} {rejectModalDoctor.user?.last_name}
              </strong>{' '}
              ({rejectModalDoctor.license_number || 'No license'}). Please state the reason for rejection:
            </p>

            <form onSubmit={handleConfirmReject} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-stone-700 uppercase tracking-wider mb-1">
                  Rejection Reason
                </label>
                <textarea
                  rows={3}
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="e.g. Invalid state medical council registration number or forged credentials..."
                  className="w-full px-3 py-2 text-xs rounded-xl border border-stone-200 bg-stone-50"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRejectModalDoctor(null)}
                  className="px-4 py-2 rounded-xl border border-stone-200 text-stone-600 text-xs font-semibold hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={doctorActionLoading || !rejectionReason.trim()}
                  className="px-5 py-2 rounded-xl bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700 disabled:opacity-50"
                >
                  {doctorActionLoading ? 'Rejecting...' : 'Confirm Rejection'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Remove Doctor Modal */}
      {removeModalDoctor && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-4 sm:p-6 max-h-[90vh] overflow-y-auto shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-stone-100 pb-3">
              <div className="flex items-center gap-2 text-rose-600">
                <UserMinus className="w-5 h-5" />
                <h4 className="text-base font-bold text-stone-900">
                  Remove Doctor from Organization
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setRemoveModalDoctor(null)}
                className="text-stone-400 hover:text-stone-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-stone-600">
              <p>
                Are you sure you want to remove <strong className="text-stone-900">Dr. {removeModalDoctor.user?.first_name} {removeModalDoctor.user?.last_name}</strong>? They will no longer be listed as an active practitioner with the organization.
              </p>
              
              <div className="p-3 bg-stone-50 rounded-xl space-y-1.5 border border-stone-200">
                <div className="flex justify-between">
                  <span className="text-stone-500">Doctor Joining Date:</span>
                  <span className="font-semibold text-stone-800">{formatDate(removeModalDoctor.joining_date)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Specialization:</span>
                  <span className="font-semibold text-stone-800">{removeModalDoctor.specialization}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Removal Effective:</span>
                  <span className="font-semibold text-rose-600">Immediately upon confirmation</span>
                </div>
              </div>

              <p className="text-[11px] text-amber-700 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                Future unbooked availability slots will be cancelled. Both the joining date and departure date will be retained in organization records.
              </p>
            </div>

            <form onSubmit={handleConfirmRemove} className="space-y-3 pt-1">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Reason for Removal / Departure (Optional):
                </label>
                <textarea
                  value={removalReason}
                  onChange={(e) => setRemovalReason(e.target.value)}
                  rows={3}
                  className="w-full text-xs p-2.5 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-rose-500 bg-stone-50 text-stone-800"
                  placeholder="e.g. Completed contract, resigned, relocated, or no longer practicing..."
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-stone-100">
                <button
                  type="button"
                  onClick={() => setRemoveModalDoctor(null)}
                  className="px-3.5 py-1.5 rounded-xl border border-stone-200 text-stone-600 text-xs font-semibold hover:bg-stone-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={doctorActionLoading}
                  className="px-4 py-1.5 rounded-xl bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700 disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
                >
                  {doctorActionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Confirm & Remove Doctor</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}


    </div>
  );
};
