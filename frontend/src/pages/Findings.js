import React, { useState, useEffect } from 'react';
import axios from 'axios';
import RemediationModal from '../components/RemediationModal';
import BulkActions from '../components/BulkActions';

function Findings() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [findings, setFindings] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [latestScanId, setLatestScanId] = useState(null);
  const [exporting, setExporting] = useState(false);
  
  // Remediation Modal
  const [showRemediationModal, setShowRemediationModal] = useState(false);
  const [selectedFindingId, setSelectedFindingId] = useState(null);
  
  // Bulk Actions
  const [selectedFindings, setSelectedFindings] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState('');
  const [frameworkFilter, setFrameworkFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [limit, setLimit] = useState(100);

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchLatestScan(selectedAccount.id);
    }
  }, [selectedAccount]);

  useEffect(() => {
    if (latestScanId) {
      fetchFindings();
    }
  }, [latestScanId, severityFilter, frameworkFilter, statusFilter, limit]);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/cloud-accounts');
      const accountsList = response.data;
      setAccounts(accountsList);
      if (accountsList.length > 0) {
        setSelectedAccount(accountsList[0]);
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error('Error fetching accounts:', error);
      setLoading(false);
    }
  };

  const fetchLatestScan = async (accountId) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/scans/account/${accountId}`
      );
      
      if (response.data.scans && response.data.scans.length > 0) {
        const latest = response.data.scans[0];
        if (latest.scan_status === 'Completed') {
          setLatestScanId(latest.scan_id);
        } else {
          setLatestScanId(null);
          setLoading(false);
        }
      } else {
        setLatestScanId(null);
        setLoading(false);
      }
    } catch (error) {
      console.error('Error fetching scans:', error);
      setLoading(false);
    }
  };

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (severityFilter) params.append('severity', severityFilter);
      if (frameworkFilter) params.append('framework', frameworkFilter);
      if (statusFilter) params.append('status', statusFilter);
      params.append('limit', limit);

      const response = await axios.get(
        `http://localhost:8000/api/scores/scan/${latestScanId}/findings?${params}`
      );
      
      setFindings(response.data.findings || []);
      setSummary(response.data.summary || {});
      setLoading(false);
    } catch (error) {
      console.error('Error fetching findings:', error);
      setLoading(false);
    }
  };

  const handleAccountChange = (e) => {
    const accountId = e.target.value;
    const account = accounts.find(a => a.id === accountId);
    setSelectedAccount(account);
  };

  const exportToCSV = async () => {
    if (!latestScanId || !selectedAccount) {
      alert('No scan available to export');
      return;
    }
    setExporting(true);
    try {
      const params = new URLSearchParams();
      if (severityFilter) params.append('severity', severityFilter);
      if (frameworkFilter) params.append('framework', frameworkFilter);
      const url = `http://localhost:8000/api/scores/scan/${latestScanId}/export/csv?${params}`;
      const link = document.createElement('a');
      link.href = url;
      link.download = `${selectedAccount.account_name}_findings_${latestScanId.substring(0, 8)}.csv`;
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

  const toggleFindingSelection = (findingId) => {
    const newSelected = new Set(selectedFindings);
    if (newSelected.has(findingId)) {
      newSelected.delete(findingId);
    } else {
      newSelected.add(findingId);
    }
    setSelectedFindings(newSelected);
    setSelectAll(newSelected.size === findings.length && findings.length > 0);
  };

  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedFindings(new Set());
      setSelectAll(false);
    } else {
      const allIds = new Set(findings.map(f => f.finding_id));
      setSelectedFindings(allIds);
      setSelectAll(true);
    }
  };

  const handleBulkAcknowledge = (selectedIds) => {
    alert(`✅ Marked ${selectedIds.length} findings as acknowledged!\n\nIn a real system, these would be updated in the database.`);
    setSelectedFindings(new Set());
    setSelectAll(false);
  };

  const handleBulkExport = async (selectedIds) => {
    try {
      const findingsToExport = findings.filter(f => selectedIds.includes(f.finding_id));
      const csv = [
        ['Check ID', 'Check Title', 'Status', 'Severity', 'Resource Type', 'Resource ID', 'Frameworks', 'Discovered At'],
        ...findingsToExport.map(f => [
          f.check_id,
          f.check_title,
          f.status,
          f.severity,
          f.resource_type,
          f.resource_id || 'N/A',
          (f.mapped_controls || []).map(c => c.framework).join('; '),
          new Date(f.discovered_at).toISOString()
        ])
      ]
        .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
        .join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `bulk_findings_export_${new Date().getTime()}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert(`✅ Exported ${selectedIds.length} findings to CSV`);
      setSelectedFindings(new Set());
      setSelectAll(false);
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export findings');
    }
  };

  const handleBulkAssign = (selectedIds, assignee) => {
    alert(`👥 Assigned ${selectedIds.length} findings to ${assignee}!\n\nIn a real system, these would be updated in the database and notifications sent.`);
    setSelectedFindings(new Set());
    setSelectAll(false);
  };

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
          <h1>Security Findings</h1>
          <p>Detailed view of security issues discovered in your environment</p>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <h3>No Accounts Found</h3>
          <p>Add a cloud account to view security findings</p>
        </div>
      </div>
    );
  }

  if (!latestScanId) {
    return (
      <div>
        <div className="page-header">
          <h1>Security Findings</h1>
          <p>Detailed view of security issues discovered in your environment</p>
        </div>
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
          <div className="empty-state-icon">🔍</div>
          <h3>No Findings Available for {selectedAccount.account_name}</h3>
          <p>Run a scan to see security findings</p>
        </div>
      </div>
    );
  }

  const failedFindings = findings.filter(f => f.status === 'Fail').length;
  const passedFindings = findings.filter(f => f.status === 'Pass').length;

  return (
    <div>
      <div className="page-header">
        <h1>Security Findings</h1>
        <p>Detailed view of security issues discovered in {selectedAccount.account_name}</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card critical">
          <div className="stat-label">Critical</div>
          <div className="stat-value">
            {summary.Critical?.Fail || 0}
          </div>
        </div>
        <div className="stat-card high">
          <div className="stat-label">High</div>
          <div className="stat-value">
            {summary.High?.Fail || 0}
          </div>
        </div>
        <div className="stat-card medium">
          <div className="stat-label">Medium</div>
          <div className="stat-value">
            {summary.Medium?.Fail || 0}
          </div>
        </div>
        <div className="stat-card low">
          <div className="stat-label">Low</div>
          <div className="stat-value">
            {summary.Low?.Fail || 0}
          </div>
        </div>
      </div>

      <BulkActions
        selectedFindings={Array.from(selectedFindings)}
        allFindings={findings}
        onAcknowledge={handleBulkAcknowledge}
        onExport={handleBulkExport}
        onAssign={handleBulkAssign}
      />

      <div className="card">
        <div className="filters">
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
            <label>Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Status</option>
              <option value="Fail">Failed Only</option>
              <option value="Pass">Passed Only</option>
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
          <div className="filter-group">
            <label>Framework</label>
            <select
              value={frameworkFilter}
              onChange={(e) => setFrameworkFilter(e.target.value)}
            >
              <option value="">All Frameworks</option>
              <option value="ISO 27001">ISO 27001</option>
              <option value="NIST CSF">NIST CSF</option>
              <option value="PCI-DSS">PCI-DSS</option>
              <option value="CIS AWS">CIS AWS</option>
              <option value="GDPR">GDPR</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Results per page</label>
            <select
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
            >
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
              <option value="500">500</option>
            </select>
          </div>
          <div className="filter-group" style={{ marginLeft: 'auto' }}>
            <label>&nbsp;</label>
            <button
              className="btn btn-primary"
              onClick={exportToCSV}
              disabled={exporting}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              {exporting ? (
                <>
                  <span className="spinner" style={{
                    width: '16px',
                    height: '16px',
                    borderWidth: '2px'
                  }}></span>
                  Exporting...
                </>
              ) : (
                <>
                  📥 Export to CSV
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong style={{ fontSize: '18px' }}>
              {findings.length} findings displayed
            </strong>
            <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#64748b' }}>
              {failedFindings} failed • {passedFindings} passed
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '14px', color: '#64748b' }}>Latest scan</div>
            <code style={{ fontSize: '13px' }}>{latestScanId.substring(0, 8)}...</code>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <input
                    type="checkbox"
                    checked={selectAll}
                    onChange={toggleSelectAll}
                    style={{ cursor: 'pointer' }}
                  />
                </th>
                <th>Check</th>
                <th>Status</th>
                <th>Severity</th>
                <th>Resource</th>
                <th>Frameworks</th>
                <th>Discovered</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((finding) => (
                <tr key={finding.finding_id} style={{
                  backgroundColor: selectedFindings.has(finding.finding_id) ? '#f0f9ff' : 'transparent'
                }}>
                  <td style={{ textAlign: 'center' }}>
                    <input
                      type="checkbox"
                      checked={selectedFindings.has(finding.finding_id)}
                      onChange={() => toggleFindingSelection(finding.finding_id)}
                      style={{ cursor: 'pointer' }}
                    />
                  </td>
                  <td>
                    <strong>{finding.check_title}</strong>
                    <br />
                    <small style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '11px' }}>
                      {finding.check_id}
                    </small>
                  </td>
                  <td>
                    <span className={`badge ${finding.status === 'Pass' ? 'pass' : 'fail'}`}>
                      {finding.status}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${finding.severity.toLowerCase()}`}>
                      {finding.severity}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontWeight: '500' }}>{finding.resource_type}</div>
                    {finding.resource_id && (
                      <small style={{ color: '#64748b', wordBreak: 'break-all', fontSize: '11px' }}>
                        {finding.resource_id.substring(0, 40)}...
                      </small>
                    )}
                  </td>
                  <td>
                    {finding.mapped_controls && finding.mapped_controls.length > 0 ? (
                      <div>
                        {[...new Set(finding.mapped_controls.map(c => c.framework))]
                          .map((fw, idx) => (
                            <span
                              key={idx}
                              className="badge"
                              style={{
                                margin: '2px',
                                fontSize: '10px',
                                background: '#e0e7ff',
                                color: '#3730a3'
                              }}
                            >
                              {fw}
                            </span>
                          ))}
                      </div>
                    ) : (
                      <span style={{ color: '#94a3b8' }}>-</span>
                    )}
                  </td>
                  <td>
                    {new Date(finding.discovered_at).toLocaleDateString()}
                  </td>
                  <td>
                    {finding.status === 'Fail' && (
                      <button
                        onClick={() => {
                          setSelectedFindingId(finding.finding_id);
                          setShowRemediationModal(true);
                        }}
                        className="btn btn-secondary"
                        style={{
                          fontSize: '12px',
                          padding: '6px 12px',
                          backgroundColor: '#3b82f6',
                          color: 'white',
                          border: 'none'
                        }}
                      >
                        🔧 Fix
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {findings.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <h3>No Findings Match Filters</h3>
          <p>Adjust your filters to see more results</p>
        </div>
      )}

      {showRemediationModal && (
        <RemediationModal
          findingId={selectedFindingId}
          onClose={() => {
            setShowRemediationModal(false);
            setSelectedFindingId(null);
          }}
        />
      )}
    </div>
  );
}

export default Findings;
