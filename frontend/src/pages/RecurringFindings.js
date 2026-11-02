import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

function RecurringFindings() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalScans, setTotalScans] = useState(0);
  const [exporting, setExporting] = useState(false);
  
  // Filters
  const [minOccurrences, setMinOccurrences] = useState(2);
  const [severityFilter, setSeverityFilter] = useState('');

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchRecurringFindings(selectedAccount.id);
    }
  }, [selectedAccount, minOccurrences, severityFilter]);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/cloud-accounts');
      const accountsList = response.data;
      setAccounts(accountsList);
      
      // Auto-select first account
      if (accountsList.length > 0) {
        setSelectedAccount(accountsList[0]);
      }
    } catch (error) {
      console.error('Error fetching accounts:', error);
      setLoading(false);
    }
  };

  const fetchRecurringFindings = async (accountId) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('min_occurrences', minOccurrences);
      if (severityFilter) params.append('severity', severityFilter);
      params.append('limit', 200);

      const response = await axios.get(
        `http://localhost:8000/api/scores/account/${accountId}/recurring-findings?${params}`
      );

      setFindings(response.data.recurring_findings || []);
      setTotalScans(response.data.total_scans_analyzed || 0);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching recurring findings:', error);
      setLoading(false);
    }
  };

  const handleAccountChange = (e) => {
    const accountId = e.target.value;
    const account = accounts.find(a => a.id === accountId);
    setSelectedAccount(account);
  };

  const exportToCSV = () => {
    if (!selectedAccount) return;
    
    setExporting(true);
    try {
      // Create CSV content
      const headers = [
        'Account',
        'Check ID',
        'Check Title',
        'Severity',
        'Resource Type',
        'Resource ID',
        'Occurrences',
        'Days Persistent',
        'First Seen',
        'Last Seen'
      ];

      const rows = findings.map(finding => [
        selectedAccount.account_name,
        finding.check_id,
        finding.check_title,
        finding.severity,
        finding.resource_type,
        finding.resource_id,
        finding.occurrence_count,
        finding.days_persistent,
        finding.first_seen,
        finding.last_seen
      ]);

      // Build CSV
      let csvContent = headers.join(',') + '\n';
      rows.forEach(row => {
        csvContent += row.map(cell => {
          const cellStr = String(cell);
          if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
            return `"${cellStr.replace(/"/g, '""')}"`;
          }
          return cellStr;
        }).join(',') + '\n';
      });

      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      link.setAttribute('href', url);
      link.setAttribute('download', `recurring_findings_${selectedAccount.account_name}_${timestamp}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setExporting(false);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export CSV: ' + error.message);
      setExporting(false);
    }
  };

  // Calculate stats
  const stats = {
    critical: findings.filter(f => f.severity === 'Critical').length,
    high: findings.filter(f => f.severity === 'High').length,
    medium: findings.filter(f => f.severity === 'Medium').length,
    low: findings.filter(f => f.severity === 'Low').length,
    total: findings.length
  };

  // Severity distribution for pie chart
  const severityData = [
    { name: 'Critical', value: stats.critical, color: '#ef4444' },
    { name: 'High', value: stats.high, color: '#f59e0b' },
    { name: 'Medium', value: stats.medium, color: '#eab308' },
    { name: 'Low', value: stats.low, color: '#22c55e' }
  ].filter(item => item.value > 0);

  // Top recurring findings for bar chart
  const topRecurring = findings
    .slice(0, 10)
    .map(f => ({
      name: f.check_title.substring(0, 30) + '...',
      occurrences: f.occurrence_count,
      severity: f.severity
    }));

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!selectedAccount) {
    return (
      <div>
        <div className="page-header">
          <h1>Recurring Findings</h1>
          <p>Track persistent security issues across multiple scans</p>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🔁</div>
          <h3>No Accounts Found</h3>
          <p>Add a cloud account to track recurring findings</p>
        </div>
      </div>
    );
  }

  if (totalScans < 2) {
    return (
      <div>
        <div className="page-header">
          <h1>Recurring Findings</h1>
          <p>Track persistent security issues across multiple scans</p>
        </div>

        {/* Account Selector */}
        <div className="card">
          <div className="filter-group">
            <label>Cloud Account</label>
            <select value={selectedAccount.id} onChange={handleAccountChange}>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.account_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="empty-state">
          <div className="empty-state-icon">🔁</div>
          <h3>Need More Scans for {selectedAccount.account_name}</h3>
          <p>Run at least 2 scans to identify recurring findings</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Recurring Findings</h1>
          <p>Security issues that persist across multiple scans</p>
        </div>
        {findings.length > 0 && (
          <button
            className="btn btn-primary"
            onClick={exportToCSV}
            disabled={exporting}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            {exporting ? (
              <>
                <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
                Exporting...
              </>
            ) : (
              <>
                📥 Export to CSV
              </>
            )}
          </button>
        )}
      </div>

      {/* Alert Banner */}
      {findings.length > 0 && (
        <div style={{
          padding: '16px',
          marginBottom: '20px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '24px' }}>🔄</span>
          <div>
            <strong style={{ color: '#991b1b' }}>
              {findings.length} Recurring Security Issues Detected in {selectedAccount.account_name}
            </strong>
            <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#7f1d1d' }}>
              These issues have appeared in {minOccurrences}+ scans and have not been resolved.
              Prioritize remediation for {stats.critical} critical and {stats.high} high severity recurring issues.
            </p>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Scans Analyzed</div>
          <div className="stat-value">{totalScans}</div>
          <div style={{ fontSize: '12px', marginTop: '4px', color: '#64748b' }}>
            {selectedAccount.account_name}
          </div>
        </div>
        <div className="stat-card critical">
          <div className="stat-label">Critical Recurring</div>
          <div className="stat-value">{stats.critical}</div>
          <div style={{ fontSize: '12px', marginTop: '4px', color: '#7f1d1d' }}>
            Immediate action required
          </div>
        </div>
        <div className="stat-card high">
          <div className="stat-label">High Recurring</div>
          <div className="stat-value">{stats.high}</div>
          <div style={{ fontSize: '12px', marginTop: '4px', color: '#78350f' }}>
            Address within 48 hours
          </div>
        </div>
        <div className="stat-card medium">
          <div className="stat-label">Medium Recurring</div>
          <div className="stat-value">{stats.medium}</div>
          <div style={{ fontSize: '12px', marginTop: '4px', color: '#713f12' }}>
            Schedule remediation
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
          <div className="filter-group">
            <label>Cloud Account</label>
            <select value={selectedAccount.id} onChange={handleAccountChange}>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.account_name}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Minimum Occurrences</label>
            <select
              value={minOccurrences}
              onChange={(e) => setMinOccurrences(parseInt(e.target.value))}
            >
              <option value="2">2+ scans</option>
              <option value="3">3+ scans</option>
              <option value="4">4+ scans</option>
              <option value="5">5+ scans</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Severity</label>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        {/* Severity Distribution */}
        <div className="card">
          <h3 className="card-title">Recurring Findings by Severity</h3>
          {severityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
              No data to display
            </div>
          )}
        </div>

        {/* Top Recurring */}
        <div className="card">
          <h3 className="card-title">Most Frequently Recurring Checks</h3>
          {topRecurring.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topRecurring} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={150} />
                <Tooltip />
                <Bar dataKey="occurrences" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
              No data to display
            </div>
          )}
        </div>
      </div>

      {/* Recurring Findings Table */}
      {findings.length > 0 ? (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              Persistent Security Issues ({findings.length})
            </h3>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Check</th>
                  <th>Severity</th>
                  <th>Resource</th>
                  <th>Occurrences</th>
                  <th>Days Persistent</th>
                  <th>First Seen</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((finding, idx) => (
                  <tr key={idx}>
                    <td>
                      <strong>{finding.check_title}</strong>
                      <br />
                      <small style={{ color: '#64748b', fontFamily: 'monospace' }}>
                        {finding.check_id}
                      </small>
                    </td>
                    <td>
                      <span className={`badge ${finding.severity.toLowerCase()}`}>
                        {finding.severity}
                      </span>
                    </td>
                    <td>
                      <div>{finding.resource_type}</div>
                      <small style={{ color: '#64748b', wordBreak: 'break-all' }}>
                        {finding.resource_id.substring(0, 40)}...
                      </small>
                    </td>
                    <td>
                      <span style={{
                        background: finding.occurrence_count >= 5 ? '#fee2e2' :
                                   finding.occurrence_count >= 3 ? '#fed7aa' : '#dbeafe',
                        color: finding.occurrence_count >= 5 ? '#991b1b' :
                               finding.occurrence_count >= 3 ? '#9a3412' : '#1e40af',
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontWeight: '600',
                        fontSize: '12px'
                      }}>
                        {finding.occurrence_count} scans
                      </span>
                    </td>
                    <td>
                      <strong style={{ color: finding.days_persistent > 7 ? '#ef4444' : '#64748b' }}>
                        {finding.days_persistent} days
                      </strong>
                    </td>
                    <td>
                      {new Date(finding.first_seen).toLocaleDateString()}
                    </td>
                    <td>
                      {new Date(finding.last_seen).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <h3>No Recurring Findings</h3>
          <p>Great! No security issues are persisting across multiple scans in {selectedAccount.account_name} with current filters.</p>
        </div>
      )}
    </div>
  );
}

export default RecurringFindings;
