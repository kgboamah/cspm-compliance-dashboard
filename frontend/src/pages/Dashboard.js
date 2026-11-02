import React, { useState, useEffect } from 'react';
import ToxicCombinations from '../components/ToxicCombinations';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';
import EmailPDFButton from '../components/EmailPDFButton';
import ExecutiveSummaryCards from '../components/ExecutiveSummaryCards';
import ComplianceHeatmap from '../components/ComplianceHeatmap';

function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [scores, setScores] = useState([]);
  const [latestScan, setLatestScan] = useState(null);
  const [error, setError] = useState(null);
  const [exportingCSV, setExportingCSV] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);

  useEffect(() => {
    fetchAllAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchAccountData(selectedAccount.id);
    }
  }, [selectedAccount]);

  const fetchAllAccounts = async () => {
    try {
      const accountsResponse = await fetch('http://localhost:8000/api/cloud-accounts');
      const accountsData = await accountsResponse.json();
      
      const accountsWithScores = await Promise.all(
        accountsData.map(async (account) => {
          try {
            const scoresResponse = await fetch(`http://localhost:8000/api/scores/account/${account.id}`);
            const scoresData = await scoresResponse.json();
            
            const avgCompliance = scoresData.scores && scoresData.scores.length > 0
              ? scoresData.scores.reduce((sum, s) => sum + parseFloat(s.overall_score), 0) / scoresData.scores.length
              : 0;
            
            return {
              ...account,
              avgCompliance: avgCompliance.toFixed(1),
              scoresCount: scoresData.scores ? scoresData.scores.length : 0
            };
          } catch (err) {
            return {
              ...account,
              avgCompliance: 0,
              scoresCount: 0
            };
          }
        })
      );

      setAccounts(accountsWithScores);
      
      const sorted = [...accountsWithScores].sort((a, b) => b.avgCompliance - a.avgCompliance);
      if (sorted.length > 0) {
        setSelectedAccount(sorted[0]);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching accounts:', err);
      setError('Failed to load accounts');
      setLoading(false);
    }
  };

  const fetchAccountData = async (accountId) => {
    try {
      const scansResponse = await fetch(`http://localhost:8000/api/scans/account/${accountId}`);
      const scansData = await scansResponse.json();

      if (scansData.scans && scansData.scans.length > 0) {
        const latest = scansData.scans[0];
        setLatestScan(latest);

        if (latest.scan_status === 'Completed') {
          const scoresResponse = await fetch(`http://localhost:8000/api/scores/scan/${latest.scan_id}`);
          const scoresData = await scoresResponse.json();
          setScores(scoresData.scores || []);
        }
      } else {
        setLatestScan(null);
        setScores([]);
      }
    } catch (err) {
      console.error('Error fetching account data:', err);
    }
  };

  const getComplianceColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#f59e0b';
    if (score >= 40) return '#eab308';
    return '#ef4444';
  };

  const getComplianceLabel = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    if (score > 0) return 'Poor';
    return 'Critical';
  };

  const exportSummaryCSV = async () => {
    if (!selectedAccount) return;
    setExportingCSV(true);
    try {
      const url = `http://localhost:8000/api/scores/account/${selectedAccount.id}/export/summary-csv`;
      const link = document.createElement('a');
      link.href = url;
      link.download = `${selectedAccount.account_name}_compliance_summary.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setExportingCSV(false);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export CSV: ' + error.message);
      setExportingCSV(false);
    }
  };

  const exportPDFReport = async () => {
    if (!selectedAccount) return;
    setExportingPDF(true);
    try {
      const url = `http://localhost:8000/api/scores/account/${selectedAccount.id}/export/pdf-report`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${selectedAccount.account_name}_compliance_report_${new Date().getTime()}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      setExportingPDF(false);
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Failed to export PDF: ' + error.message);
      setExportingPDF(false);
    }
  };

  const calculateOverallStats = () => {
    if (scores.length === 0) return { critical: 0, high: 0, medium: 0, low: 0, total: 0, totalFailed: 0, totalPassed: 0 };
    
    const stats = scores.reduce((acc, score) => {
      acc.critical += score.critical_findings || 0;
      acc.high += score.high_findings || 0;
      acc.medium += score.medium_findings || 0;
      acc.low += score.low_findings || 0;
      acc.totalFailed += score.controls_failed || 0;
      acc.totalPassed += score.controls_passed || 0;
      return acc;
    }, { critical: 0, high: 0, medium: 0, low: 0, totalFailed: 0, totalPassed: 0 });

    stats.total = stats.critical + stats.high + stats.medium + stats.low;
    return stats;
  };

  const stats = calculateOverallStats();

  const severityData = [
    { name: 'Critical', value: stats.critical, color: '#ef4444' },
    { name: 'High', value: stats.high, color: '#f59e0b' },
    { name: 'Medium', value: stats.medium, color: '#eab308' },
    { name: 'Low', value: stats.low, color: '#22c55e' }
  ].filter(item => item.value > 0);

  const frameworkFindingsData = scores.map(score => ({
    name: score.framework,
    Critical: score.critical_findings,
    High: score.high_findings,
    Medium: score.medium_findings,
    Low: score.low_findings,
    Failed: score.controls_failed,
    Passed: score.controls_passed
  }));

  const controlsStatusData = [
    { name: 'Failed', value: stats.totalFailed, color: '#ef4444' },
    { name: 'Passed', value: stats.totalPassed, color: '#22c55e' }
  ].filter(item => item.value > 0);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <h3>{error}</h3>
        <button className="btn btn-primary" onClick={fetchAllAccounts}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Multi-Account Security Dashboard</h1>
          <p>Comprehensive compliance monitoring across all cloud accounts</p>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        {accounts.map((account) => {
          const isSelected = selectedAccount && selectedAccount.id === account.id;
          const compliance = parseFloat(account.avgCompliance);
          
          return (
            <div
              key={account.id}
              onClick={() => setSelectedAccount(account)}
              style={{
                padding: '20px',
                borderRadius: '12px',
                border: isSelected ? `3px solid ${getComplianceColor(compliance)}` : '2px solid #e2e8f0',
                backgroundColor: isSelected ? '#f8fafc' : 'white',
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: isSelected ? '0 4px 12px rgba(0,0,0,0.1)' : '0 1px 3px rgba(0,0,0,0.05)',
                transform: isSelected ? 'translateY(-2px)' : 'none'
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.08)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)';
                  e.currentTarget.style.transform = 'none';
                }
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                <div>
                  <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: '600' }}>
                    {account.account_name}
                  </h4>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>
                    {account.cloud_provider} • {account.account_id}
                  </p>
                </div>
                {isSelected && (
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    backgroundColor: getComplianceColor(compliance),
                    color: 'white',
                    fontSize: '11px',
                    fontWeight: '600'
                  }}>
                    ACTIVE
                  </span>
                )}
              </div>
              
              <div style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', color: '#64748b' }}>Avg Compliance</span>
                  <span style={{ 
                    fontSize: '13px', 
                    fontWeight: '600',
                    color: getComplianceColor(compliance)
                  }}>
                    {getComplianceLabel(compliance)}
                  </span>
                </div>
                <div style={{
                  height: '8px',
                  backgroundColor: '#e2e8f0',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${compliance}%`,
                    backgroundColor: getComplianceColor(compliance),
                    transition: 'width 0.3s'
                  }}></div>
                </div>
              </div>

              <div style={{
                fontSize: '28px',
                fontWeight: '700',
                color: getComplianceColor(compliance),
                marginTop: '8px'
              }}>
                {compliance}%
              </div>
              
              <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                {account.scoresCount} frameworks assessed
              </div>
            </div>
          );
        })}
      </div>

      {selectedAccount && <ExecutiveSummaryCards accountId={selectedAccount.id} selectedAccount={selectedAccount} />}

      {accounts.length > 0 && <ComplianceHeatmap accounts={accounts} />}

      {selectedAccount && (
        <>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-secondary"
              onClick={exportSummaryCSV}
              disabled={exportingCSV || !latestScan}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              {exportingCSV ? (
                <>
                  <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
                  Exporting...
                </>
              ) : (
                <>📊 Export CSV</>
              )}
            </button>
            <button
              className="btn btn-primary"
              onClick={exportPDFReport}
              disabled={exportingPDF || !latestScan}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              {exportingPDF ? (
                <>
                  <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
                  Generating...
                </>
              ) : (
                <>📄 Download PDF Report</>
              )}
            </button>
          </div>

          {!latestScan ? (
            <div className="empty-state">
              <div className="empty-state-icon">🔍</div>
              <h3>No Scans Found for {selectedAccount.account_name}</h3>
              <p>Run a security scan to view compliance scores</p>
              <button className="btn btn-primary" onClick={() => navigate('/scans')}>
                Start New Scan
              </button>
            </div>
          ) : (
            <>
              {stats.totalPassed === 0 && stats.totalFailed > 0 && (
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
                  <span style={{ fontSize: '24px' }}>⚠️</span>
                  <div>
                    <strong style={{ color: '#991b1b' }}>Action Required: Security Issues Detected</strong>
                    <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#7f1d1d' }}>
                      {selectedAccount.account_name} has {stats.total} security findings across {stats.totalFailed} failed controls.
                      Immediate remediation recommended for {stats.critical} critical and {stats.high} high severity issues.
                    </p>
                  </div>
                </div>
              )}

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Latest Scan - {selectedAccount.account_name}</h3>
                  <span className="badge pass">{latestScan.scan_status}</span>
                </div>
                <div style={{ display: 'flex', gap: '20px', fontSize: '14px', color: '#64748b' }}>
                  <div><strong>Scan ID:</strong> {latestScan.scan_id.substring(0, 8)}...</div>
                  <div><strong>Completed:</strong> {new Date(latestScan.completed_at).toLocaleString()}</div>
                  <div><strong>Total Checks:</strong> {latestScan.total_checks_run}</div>
                </div>
              </div>

              <div className="stats-grid">
                <div className="stat-card critical">
                  <div className="stat-label">Critical Findings</div>
                  <div className="stat-value">{stats.critical}</div>
                  <div style={{ fontSize: '12px', marginTop: '8px', color: '#7f1d1d' }}>
                    Requires immediate action
                  </div>
                </div>
                <div className="stat-card high">
                  <div className="stat-label">High Findings</div>
                  <div className="stat-value">{stats.high}</div>
                  <div style={{ fontSize: '12px', marginTop: '8px', color: '#78350f' }}>
                    Address within 24-48 hours
                  </div>
                </div>
                <div className="stat-card medium">
                  <div className="stat-label">Medium Findings</div>
                  <div className="stat-value">{stats.medium}</div>
                  <div style={{ fontSize: '12px', marginTop: '8px', color: '#713f12' }}>
                    Schedule remediation
                  </div>
                </div>
                <div className="stat-card low">
                  <div className="stat-label">Low Findings</div>
                  <div className="stat-value">{stats.low}</div>
                  <div style={{ fontSize: '12px', marginTop: '8px', color: '#14532d' }}>
                    Monitor and track
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
                <div className="card">
                  <h3 className="card-title">Security Findings by Severity</h3>
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
                </div>

                <div className="card">
                  <h3 className="card-title">Control Compliance Status</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={controlsStatusData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {controlsStatusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '14px', color: '#64748b' }}>
                    <strong style={{ fontSize: '32px', color: stats.totalPassed === 0 ? '#ef4444' : '#22c55e', display: 'block' }}>
                      {stats.totalFailed > 0 ? ((stats.totalPassed / (stats.totalPassed + stats.totalFailed)) * 100).toFixed(1) : 0}%
                    </strong>
                    Overall Compliance Rate
                  </div>
                </div>
              </div>

              <div className="card" style={{ marginBottom: '20px' }}>
                <h3 className="card-title">Findings by Framework</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={frameworkFindingsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Critical" stackId="a" fill="#ef4444" />
                    <Bar dataKey="High" stackId="a" fill="#f59e0b" />
                    <Bar dataKey="Medium" stackId="a" fill="#eab308" />
                    <Bar dataKey="Low" stackId="a" fill="#22c55e" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <ToxicCombinations accountId={selectedAccount.id} />

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Framework Compliance Details</h3>
                  <button className="btn btn-primary" onClick={() => navigate('/frameworks')}>
                    View All Frameworks
                  </button>
                </div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Framework</th>
                        <th>Compliance Rate</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>N/A</th>
                        <th>Total Controls</th>
                        <th>Critical</th>
                        <th>High</th>
                        <th>Medium</th>
                        <th>Low</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scores.map((score, index) => {
                        const complianceRate = score.total_controls > 0
                          ? ((score.controls_passed / score.total_controls) * 100).toFixed(1)
                          : 0;
                        return (
                          <tr key={index}>
                            <td><strong>{score.framework}</strong></td>
                            <td>
                              <span style={{
                                color: complianceRate > 80 ? '#22c55e' :
                                       complianceRate > 50 ? '#f59e0b' : '#ef4444',
                                fontWeight: 'bold'
                              }}>
                                {complianceRate}%
                              </span>
                            </td>
                            <td><span className="badge pass">{score.controls_passed}</span></td>
                            <td><span className="badge fail">{score.controls_failed}</span></td>
                            <td>{score.controls_not_applicable}</td>
                            <td>{score.total_controls}</td>
                            <td><span className="badge critical">{score.critical_findings}</span></td>
                            <td><span className="badge high">{score.high_findings}</span></td>
                            <td><span className="badge medium">{score.medium_findings}</span></td>
                            <td><span className="badge low">{score.low_findings}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <EmailPDFButton accountId={selectedAccount.id} />

              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                <button className="btn btn-primary" onClick={() => navigate('/findings')}>
                  View All Findings ({stats.total})
                </button>
                <button className="btn btn-secondary" onClick={() => navigate('/scans')}>
                  Run New Scan
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default Dashboard;
