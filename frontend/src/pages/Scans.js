import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Scans() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchScans(selectedAccount.id);
      const interval = setInterval(() => fetchScans(selectedAccount.id), 10000);
      return () => clearInterval(interval);
    }
  }, [selectedAccount]);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/cloud-accounts');
      const accountsList = response.data;
      setAccounts(accountsList);
      
      // Auto-select first account
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

  const fetchScans = async (accountId) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/scans/account/${accountId}`
      );
      setScans(response.data.scans || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching scans:', error);
      setLoading(false);
    }
  };

  const handleAccountChange = (e) => {
    const accountId = e.target.value;
    const account = accounts.find(a => a.id === accountId);
    setSelectedAccount(account);
  };

  const startScan = async () => {
    if (starting || !selectedAccount) return;
    
    setStarting(true);
    try {
      await axios.post('http://localhost:8000/api/scans/start', {
        account_id: selectedAccount.id
      });
      alert(`Scan started successfully for ${selectedAccount.account_name}!`);
      fetchScans(selectedAccount.id);
    } catch (error) {
      console.error('Error starting scan:', error);
      alert('Failed to start scan: ' + error.message);
    } finally {
      setStarting(false);
    }
  };

  const calculateScores = async (scanId) => {
    try {
      await axios.post(
        `http://localhost:8000/api/scores/${scanId}/calculate`
      );
      alert('Scores calculated successfully!');
      fetchScans(selectedAccount.id);
    } catch (error) {
      console.error('Error calculating scores:', error);
      alert('Failed to calculate scores: ' + error.message);
    }
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
          <h1>Security Scans</h1>
          <p>Manage and monitor Prowler security scans</p>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <h3>No Accounts Found</h3>
          <p>Add a cloud account to start running security scans</p>
        </div>
      </div>
    );
  }

  // Calculate stats
  const stats = {
    total: scans.length,
    completed: scans.filter(s => s.scan_status === 'Completed').length,
    running: scans.filter(s => s.scan_status === 'Running').length,
    failed: scans.filter(s => s.scan_status === 'Failed').length
  };

  return (
    <div>
      <div className="page-header">
        <h1>Security Scans</h1>
        <p>Manage and monitor Prowler security scans</p>
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

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Scans</div>
          <div className="stat-value">{stats.total}</div>
          <div style={{ fontSize: '12px', marginTop: '4px', color: '#64748b' }}>
            {selectedAccount.account_name}
          </div>
        </div>
        <div className="stat-card pass">
          <div className="stat-label">Completed</div>
          <div className="stat-value">{stats.completed}</div>
        </div>
        <div className="stat-card medium">
          <div className="stat-label">Running</div>
          <div className="stat-value">{stats.running}</div>
        </div>
        <div className="stat-card fail">
          <div className="stat-label">Failed</div>
          <div className="stat-value">{stats.failed}</div>
        </div>
      </div>

      {/* Start New Scan */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Start New Scan</h3>
        </div>
        <p>
          Run a comprehensive security scan for <strong>{selectedAccount.account_name}</strong>.
          Scans typically take 1-2 minutes to complete.
        </p>
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#fef3c7', 
          border: '1px solid #fbbf24',
          borderRadius: '6px',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          ⚠️ <strong>Note:</strong> This account contains synthetic data. Real Prowler scans require valid AWS credentials.
        </div>
        <button
          className="btn btn-primary"
          onClick={startScan}
          disabled={starting}
        >
          {starting ? 'Starting...' : '🔍 Start New Scan'}
        </button>
      </div>

      {/* Scan History */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Scan History - {selectedAccount.account_name}</h3>
          <span style={{
            padding: '6px 12px',
            borderRadius: '6px',
            backgroundColor: '#f1f5f9',
            fontSize: '14px',
            fontWeight: '600',
            color: '#475569'
          }}>
            {scans.length} scans
          </span>
        </div>
        
        {scans.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Scan ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Started</th>
                  <th>Completed</th>
                  <th>Checks Run</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((scan) => {
                  const duration = scan.started_at && scan.completed_at
                    ? Math.round((new Date(scan.completed_at) - new Date(scan.started_at)) / 60000)
                    : null;
                  
                  return (
                    <tr key={scan.scan_id}>
                      <td>
                        <code>{scan.scan_id.substring(0, 8)}...</code>
                      </td>
                      <td>
                        <span style={{ fontSize: '13px', color: '#64748b' }}>
                          {scan.scan_type || 'Security Scan'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${
                          scan.scan_status === 'Completed' ? 'pass' :
                          scan.scan_status === 'Failed' ? 'fail' : 'medium'
                        }`}>
                          {scan.scan_status}
                        </span>
                      </td>
                      <td>{new Date(scan.started_at).toLocaleString()}</td>
                      <td>
                        {scan.completed_at
                          ? new Date(scan.completed_at).toLocaleString()
                          : '-'}
                      </td>
                      <td>
                        <strong>{scan.total_checks_run || '-'}</strong>
                      </td>
                      <td>
                        {duration !== null ? (
                          <span style={{ color: '#64748b' }}>
                            {duration} min{duration !== 1 ? 's' : ''}
                          </span>
                        ) : '-'}
                      </td>
                      <td>
                        {scan.scan_status === 'Completed' && (
                          <button
                            className="btn btn-secondary"
                            onClick={() => calculateScores(scan.scan_id)}
                            style={{ fontSize: '12px', padding: '6px 12px' }}
                          >
                            Calculate Scores
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <h3>No Scans Yet</h3>
            <p>Start your first security scan for {selectedAccount.account_name}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Scans;
