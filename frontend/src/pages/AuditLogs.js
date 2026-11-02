/**
 * Audit Logs Page - Admin Only
 * Location: frontend/src/pages/AuditLogs.js
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

function AuditLogs() {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [filters, setFilters] = useState({
    event_type: '',
    event_category: '',
    status: '',
    days: 7
  });

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchLogs();
      fetchStats();
    }
  }, [page, filters, user]);

  const fetchLogs = async () => {
    try {
      const token = localStorage.getItem('cspm_auth_token');
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '50',
        days: filters.days.toString()
      });
      
      if (filters.event_type) params.append('event_type', filters.event_type);
      if (filters.event_category) params.append('event_category', filters.event_category);
      if (filters.status) params.append('status', filters.status);
      
      const response = await axios.get(
        `http://localhost:8000/api/audit-logs/?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setLogs(response.data.logs);
      setTotal(response.data.total);
      setTotalPages(response.data.total_pages);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
      setError('Failed to load audit logs');
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('cspm_auth_token');
      const response = await axios.get(
        `http://localhost:8000/api/audit-logs/stats?days=${filters.days}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const handleExportCSV = async () => {
    try {
      const token = localStorage.getItem('cspm_auth_token');
      const response = await axios.get(
        `http://localhost:8000/api/audit-logs/export/csv?days=${filters.days}`,
        { 
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_logs_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error exporting CSV:', err);
      alert('Failed to export audit logs');
    }
  };

  const getEventBadgeColor = (eventType) => {
    const colors = {
      'login': '#22c55e',
      'login_failed': '#ef4444',
      'logout': '#64748b',
      'password_changed': '#f59e0b',
      'password_reset': '#f59e0b',
      'mfa_enabled': '#3b82f6',
      'mfa_disabled': '#8b5cf6',
      'account_created': '#10b981',
      'account_deleted': '#ef4444'
    };
    return colors[eventType] || '#64748b';
  };

  const getStatusIcon = (status) => {
    return status === 'success' ? '✓' : status === 'failure' ? '✗' : '⚠';
  };

  if (user?.role !== 'admin') {
    return (
      <div>
        <div className="page-header">
          <h1>Access Denied</h1>
          <p>Admin access required to view audit logs</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Audit Logs</h1>
        <p>Security event audit trail for all user actions</p>
      </div>

      {error && (
        <div style={{ padding: '12px', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <div className="card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '4px' }}>Total Events</div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#1e293b' }}>{stats.total_events}</div>
          </div>
          <div className="card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '4px' }}>Failed Logins</div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444' }}>{stats.failed_logins}</div>
          </div>
          <div className="card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '4px' }}>Time Period</div>
            <div style={{ fontSize: '28px', fontWeight: '700', color: '#3b82f6' }}>{stats.time_period_days}d</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '4px' }}>Time Range</label>
            <select
              value={filters.days}
              onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
              style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
            >
              <option value="1">Last 24 hours</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '4px' }}>Event Type</label>
            <select
              value={filters.event_type}
              onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
              style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
            >
              <option value="">All Types</option>
              <option value="login">Login</option>
              <option value="login_failed">Failed Login</option>
              <option value="logout">Logout</option>
              <option value="password_changed">Password Changed</option>
              <option value="mfa_enabled">MFA Enabled</option>
              <option value="mfa_disabled">MFA Disabled</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '4px' }}>Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
            >
              <option value="">All Statuses</option>
              <option value="success">Success</option>
              <option value="failure">Failure</option>
              <option value="warning">Warning</option>
            </select>
          </div>

          <div style={{ marginLeft: 'auto', paddingTop: '20px' }}>
            <button
              onClick={handleExportCSV}
              className="btn btn-secondary"
              style={{ fontSize: '14px' }}
            >
              📥 Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#64748b' }}>Timestamp</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#64748b' }}>User</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#64748b' }}>Event</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#64748b' }}>Description</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#64748b' }}>IP Address</th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#64748b' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.log_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '12px', fontSize: '13px', color: '#475569' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '12px', fontSize: '13px', color: '#1e293b', fontWeight: '500' }}>
                    {log.user_email || 'System'}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                      backgroundColor: getEventBadgeColor(log.event_type) + '20',
                      color: getEventBadgeColor(log.event_type)
                    }}>
                      {log.event_type.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '12px', fontSize: '13px', color: '#475569' }}>
                    {log.event_description}
                  </td>
                  <td style={{ padding: '12px', fontSize: '13px', color: '#64748b', fontFamily: 'monospace' }}>
                    {log.ip_address || 'N/A'}
                  </td>
                  <td style={{ padding: '12px', fontSize: '16px' }}>
                    <span title={log.status}>{getStatusIcon(log.status)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ padding: '16px', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '14px', color: '#64748b' }}>
              Showing {((page - 1) * 50) + 1} to {Math.min(page * 50, total)} of {total} logs
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary"
                style={{ fontSize: '14px' }}
              >
                Previous
              </button>
              <span style={{ padding: '8px 16px', fontSize: '14px', color: '#64748b' }}>
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn btn-secondary"
                style={{ fontSize: '14px' }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AuditLogs;
