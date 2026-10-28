import React, { useState, useEffect } from 'react';
import { getAuditLogs } from '../../api/audit';
import {
  ShieldAlert,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  RefreshCw,
  Eye,
  X
} from 'lucide-react';

export const AdminAuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);
  const [error, setError] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (actionFilter) params.action = actionFilter;
      if (resourceFilter) params.resource_type = resourceFilter;

      const data = await getAuditLogs(params);
      setLogs(data.results || data);
    } catch (err) {
      setError('Failed to fetch audit trails. Administrator authorization required.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, resourceFilter]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100 text-purple-900 text-xs font-semibold mb-3">
            <ShieldAlert className="w-3.5 h-3.5 text-purple-700" />
            <span>Append-Only Forensic Trails</span>
          </div>
          <h1 className="text-3xl font-bold font-heading text-stone-900 tracking-tight">
            Security & Clinical Audit Logs
          </h1>
          <p className="text-sm text-stone-600 mt-1">
            Immutable application-level audit events capturing logins, booking claims, state transitions, and access attempts
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-stone-200 bg-white text-stone-700 hover:bg-stone-50 text-xs font-semibold shadow-sm transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Logs</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-stone-200 shadow-sm flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="w-full sm:w-auto px-3.5 py-2 rounded-xl border border-stone-200 text-xs bg-stone-50 text-stone-700"
        >
          <option value="">All Actions</option>
          <option value="AUTH_LOGIN">AUTH_LOGIN</option>
          <option value="AUTH_REGISTER">AUTH_REGISTER</option>
          <option value="AUTH_LOGOUT">AUTH_LOGOUT</option>
          <option value="BOOKING_CREATED">BOOKING_CREATED</option>
          <option value="BOOKING_CANCELLED">BOOKING_CANCELLED</option>
          <option value="CONSULTATION_STARTED">CONSULTATION_STARTED</option>
          <option value="CONSULTATION_COMPLETED">CONSULTATION_COMPLETED</option>
          <option value="PRESCRIPTION_CREATED">PRESCRIPTION_CREATED</option>
          <option value="PAYMENT_PROCESSED">PAYMENT_PROCESSED</option>
          <option value="ACCESS_REJECTED">ACCESS_REJECTED</option>
        </select>

        <select
          value={resourceFilter}
          onChange={(e) => setResourceFilter(e.target.value)}
          className="w-full sm:w-auto px-3.5 py-2 rounded-xl border border-stone-200 text-xs bg-stone-50 text-stone-700"
        >
          <option value="">All Resource Types</option>
          <option value="USER">USER</option>
          <option value="CONSULTATION">CONSULTATION</option>
          <option value="AVAILABILITY_SLOT">AVAILABILITY_SLOT</option>
          <option value="PRESCRIPTION">PRESCRIPTION</option>
          <option value="PAYMENT">PAYMENT</option>
          <option value="ENDPOINT">ENDPOINT</option>
        </select>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-stone-400">Loading audit log entries...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-stone-500">
            No audit records match the current filter selection.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] text-left text-xs">
              <thead className="bg-stone-50 border-b border-stone-200 text-stone-600 uppercase font-semibold">
                <tr>
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4">IP Address</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {logs.map((log) => {
                  const isSuccess = log.outcome === 'SUCCESS';

                  return (
                    <tr key={log.id} className="hover:bg-stone-50/50">
                      <td className="py-3 px-4 font-mono text-stone-600">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-medium text-stone-900">
                        {log.actor_email || 'Anonymous'}
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-[10px] font-bold uppercase text-stone-600 bg-stone-100 px-2 py-0.5 rounded">
                          {log.actor_role || 'PUBLIC'}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold text-[#1C3E2D]">
                        {log.action}
                      </td>
                      <td className="py-3 px-4 text-stone-600">
                        {log.resource_type}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          isSuccess
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {isSuccess ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {log.outcome}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-stone-500">
                        {log.ip_address || '127.0.0.1'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-600 hover:text-stone-900"
                          title="Inspect metadata payload"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/60 backdrop-blur-sm p-3 sm:p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-lg w-full p-4 sm:p-6 max-h-[85vh] overflow-y-auto shadow-2xl border border-stone-200 relative animate-in fade-in duration-200 space-y-4">
            
            <button
              onClick={() => setSelectedLog(null)}
              className="absolute right-4 top-4 p-1.5 rounded-xl text-stone-400 hover:bg-stone-100"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <div className="text-xs font-bold text-[#2B5B41] uppercase tracking-wider">
                Audit Log Inspection
              </div>
              <h3 className="text-lg font-bold font-heading text-stone-900 mt-1 break-all">
                {selectedLog.action}
              </h3>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-stone-100">
                <span className="text-stone-500 font-medium">Log ID:</span>
                <span className="font-mono text-stone-800 break-all">{selectedLog.id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-stone-100">
                <span className="text-stone-500 font-medium">Request ID:</span>
                <span className="font-mono text-stone-800 break-all">{selectedLog.request_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-stone-100">
                <span className="text-stone-500 font-medium">Resource ID:</span>
                <span className="font-mono text-stone-800 break-all">{selectedLog.resource_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-stone-100">
                <span className="text-stone-500 font-medium">Timestamp:</span>
                <span className="text-stone-800">{new Date(selectedLog.timestamp).toISOString()}</span>
              </div>
            </div>

            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-stone-600 mb-2">
                Sanitized Metadata
              </div>
              <pre className="p-3 bg-stone-900 text-emerald-400 rounded-xl text-[11px] overflow-x-auto font-mono whitespace-pre-wrap break-all">
                {JSON.stringify(selectedLog.sanitized_metadata || {}, null, 2)}
              </pre>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 rounded-xl bg-stone-800 hover:bg-stone-900 text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
