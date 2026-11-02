import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Frameworks() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [latestScanId, setLatestScanId] = useState(null);
  
  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedFramework, setSelectedFramework] = useState(null);
  const [controls, setControls] = useState([]);
  const [loadingControls, setLoadingControls] = useState(false);
  
  // Expanded controls state
  const [expandedControls, setExpandedControls] = useState(new Set());

  const toggleControlExpanded = (controlId) => {
    setExpandedControls(prev => {
      const newSet = new Set(prev);
      if (newSet.has(controlId)) {
        newSet.delete(controlId);
      } else {
        newSet.add(controlId);
      }
      return newSet;
    });
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchLatestScan(selectedAccount.id);
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

  const fetchLatestScan = async (accountId) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/scans/account/${accountId}`
      );
      if (response.data.scans && response.data.scans.length > 0) {
        const latest = response.data.scans[0];
        if (latest.scan_status === 'Completed') {
          setLatestScanId(latest.scan_id);
          fetchScores(latest.scan_id);
        } else {
          setLatestScanId(null);
          setScores([]);
        }
      } else {
        setLatestScanId(null);
        setScores([]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching scans:', error);
      setLoading(false);
    }
  };

  const fetchScores = async (scanId) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/scores/scan/${scanId}`
      );
      setScores(response.data.scores || []);
    } catch (error) {
      console.error('Error fetching scores:', error);
    }
  };

  const handleAccountChange = (e) => {
    const accountId = e.target.value;
    const account = accounts.find(a => a.id === accountId);
    setSelectedAccount(account);
    closeSidebar(); // Close sidebar when switching accounts
  };

  const viewFrameworkControls = async (framework) => {
    setSelectedFramework(framework);
    setSidebarOpen(true);
    setLoadingControls(true);
    
    try {
      // Fetch findings for this framework to map to controls
      const response = await axios.get(
        `http://localhost:8000/api/scores/scan/${latestScanId}/findings?framework=${encodeURIComponent(framework.framework)}&limit=1000`
      );

      // Group findings by control
      const findingsByControl = {};
      response.data.findings.forEach(finding => {
        if (finding.mapped_controls) {
          finding.mapped_controls.forEach(control => {
            if (control.framework === framework.framework) {
              const key = control.control_id;
              if (!findingsByControl[key]) {
                findingsByControl[key] = {
                  control_id: control.control_id,
                  control_title: control.control_title,
                  findings: []
                };
              }
              findingsByControl[key].findings.push(finding);
            }
          });
        }
      });

      setControls(Object.values(findingsByControl));
      setLoadingControls(false);
    } catch (error) {
      console.error('Error fetching framework details:', error);
      setLoadingControls(false);
    }
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
    setTimeout(() => {
      setSelectedFramework(null);
      setControls([]);
      setExpandedControls(new Set());
    }, 300);
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
          <h1>Compliance Frameworks</h1>
          <p>View detailed control status for each framework</p>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <h3>No Accounts Found</h3>
          <p>Add a cloud account to view compliance frameworks</p>
        </div>
      </div>
    );
  }

  if (!latestScanId || scores.length === 0) {
    return (
      <div>
        <div className="page-header">
          <h1>Compliance Frameworks</h1>
          <p>View detailed control status for each framework</p>
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
          <div className="empty-state-icon">📋</div>
          <h3>No Framework Scores Available</h3>
          <p>Run a scan for {selectedAccount.account_name} to view compliance frameworks</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Compliance Frameworks</h1>
        <p>Detailed control status for {selectedAccount.account_name}</p>
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

      {/* Framework Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        {scores.map((score, idx) => (
          <div className="card" key={idx}>
            <h3 style={{ marginBottom: '12px', color: '#1e293b' }}>
              {score.framework}
            </h3>
            
            <div style={{ marginBottom: '20px' }}>
              <div style={{
                fontSize: '48px',
                fontWeight: 'bold',
                color: score.overall_score > 80 ? '#22c55e' :
                       score.overall_score > 50 ? '#f59e0b' : '#ef4444'
              }}>
                {score.overall_score.toFixed(0)}%
              </div>
              <div style={{ color: '#64748b', fontSize: '14px' }}>
                Compliance Score
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#64748b' }}>Passed</span>
                <span style={{ fontWeight: '600' }}>{score.controls_passed}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#64748b' }}>Failed</span>
                <span style={{ fontWeight: '600' }}>{score.controls_failed}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#64748b' }}>N/A</span>
                <span style={{ fontWeight: '600' }}>{score.controls_not_applicable}</span>
              </div>
            </div>

            <div style={{ marginBottom: '20px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '8px' }}>
                Findings by Severity
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {score.critical_findings > 0 && (
                  <span className="badge critical">
                    {score.critical_findings} Critical
                  </span>
                )}
                {score.high_findings > 0 && (
                  <span className="badge high">
                    {score.high_findings} High
                  </span>
                )}
                {score.medium_findings > 0 && (
                  <span className="badge medium">
                    {score.medium_findings} Medium
                  </span>
                )}
                {score.low_findings > 0 && (
                  <span className="badge low">
                    {score.low_findings} Low
                  </span>
                )}
              </div>
            </div>

            <button
              className="btn btn-primary"
              onClick={() => viewFrameworkControls(score)}
              style={{ width: '100%' }}
            >
              View Controls
            </button>
          </div>
        ))}
      </div>

      {/* Slide-out Sidebar */}
      {sidebarOpen && (
        <>
          {/* Overlay */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 1000,
              animation: 'fadeIn 0.3s'
            }}
            onClick={closeSidebar}
          />

          {/* Sidebar */}
          <div style={{
            position: 'fixed',
            top: 0,
            right: 0,
            bottom: 0,
            width: '600px',
            maxWidth: '90vw',
            backgroundColor: 'white',
            boxShadow: '-2px 0 8px rgba(0, 0, 0, 0.1)',
            zIndex: 1001,
            overflowY: 'auto',
            animation: 'slideIn 0.3s'
          }}>
            {/* Sidebar Header */}
            <div style={{
              padding: '24px',
              borderBottom: '1px solid #e2e8f0',
              position: 'sticky',
              top: 0,
              backgroundColor: 'white',
              zIndex: 10
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1e293b', marginBottom: '4px' }}>
                    {selectedFramework?.framework}
                  </h2>
                  <p style={{ color: '#64748b', fontSize: '14px' }}>
                    {controls.length} Controls with Findings • {selectedAccount.account_name}
                  </p>
                </div>
                <button
                  onClick={closeSidebar}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '24px',
                    cursor: 'pointer',
                    color: '#64748b',
                    padding: '8px'
                  }}
                >
                  ✕
                </button>
              </div>

              {/* Framework Summary */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '12px',
                marginTop: '16px'
              }}>
                <div style={{ textAlign: 'center', padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#22c55e' }}>
                    {selectedFramework?.controls_passed}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>Passed</div>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#ef4444' }}>
                    {selectedFramework?.controls_failed}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>Failed</div>
                </div>
                <div style={{ textAlign: 'center', padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#94a3b8' }}>
                    {selectedFramework?.controls_not_applicable}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>N/A</div>
                </div>
              </div>
            </div>

            {/* Controls List */}
            <div style={{ padding: '24px' }}>
              {loadingControls ? (
                <div className="loading">
                  <div className="spinner"></div>
                </div>
              ) : (
                controls.map((control, idx) => {
                  const criticalCount = control.findings.filter(f => f.severity === 'Critical').length;
                  const highCount = control.findings.filter(f => f.severity === 'High').length;
                  const mediumCount = control.findings.filter(f => f.severity === 'Medium').length;
                  const lowCount = control.findings.filter(f => f.severity === 'Low').length;
                  const uniqueChecks = [...new Set(control.findings.map(f => f.check_id))];
                  const isExpanded = expandedControls.has(control.control_id);

                  return (
                    <div
                      key={idx}
                      style={{
                        padding: '16px',
                        marginBottom: '12px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px',
                        backgroundColor: '#fafafa'
                      }}
                    >
                      <div style={{ marginBottom: '12px' }}>
                        <div style={{
                          fontSize: '12px',
                          fontWeight: '600',
                          color: '#3b82f6',
                          marginBottom: '4px'
                        }}>
                          {control.control_id}
                        </div>
                        <div style={{
                          fontSize: '14px',
                          fontWeight: '500',
                          color: '#1e293b'
                        }}>
                          {control.control_title}
                        </div>
                      </div>

                      <div style={{ marginBottom: '12px' }}>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '6px' }}>
                          Findings ({control.findings.length})
                        </div>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                          {criticalCount > 0 && (
                            <span className="badge critical" style={{ fontSize: '11px' }}>
                              {criticalCount} Critical
                            </span>
                          )}
                          {highCount > 0 && (
                            <span className="badge high" style={{ fontSize: '11px' }}>
                              {highCount} High
                            </span>
                          )}
                          {mediumCount > 0 && (
                            <span className="badge medium" style={{ fontSize: '11px' }}>
                              {mediumCount} Medium
                            </span>
                          )}
                          {lowCount > 0 && (
                            <span className="badge low" style={{ fontSize: '11px' }}>
                              {lowCount} Low
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Mapped checks */}
                      <div>
                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>
                          Mapped Checks ({uniqueChecks.length} unique checks, {control.findings.length} findings)
                        </div>
                        {uniqueChecks.slice(0, isExpanded ? uniqueChecks.length : 3).map((checkId, i) => {
                          const checkFindings = control.findings.filter(f => f.check_id === checkId);
                          const isCheckExpanded = expandedControls.has(`${control.control_id}-${checkId}`);

                          return (
                            <div key={i} style={{ marginBottom: '8px' }}>
                              <div
                                style={{
                                  fontSize: '11px',
                                  color: '#475569',
                                  fontFamily: 'monospace',
                                  marginBottom: '2px',
                                  padding: '4px 8px',
                                  backgroundColor: '#f1f5f9',
                                  borderRadius: '4px',
                                  marginTop: '2px',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center'
                                }}
                              >
                                <span>• {checkId}</span>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                  <span style={{
                                    fontSize: '10px',
                                    color: '#64748b',
                                    fontWeight: '500'
                                  }}>
                                    ({checkFindings.length} {checkFindings.length === 1 ? 'finding' : 'findings'})
                                  </span>
                                  <button
                                    onClick={() => toggleControlExpanded(`${control.control_id}-${checkId}`)}
                                    style={{
                                      fontSize: '10px',
                                      color: '#3b82f6',
                                      background: 'none',
                                      border: 'none',
                                      cursor: 'pointer',
                                      padding: '2px 4px',
                                      textDecoration: 'underline'
                                    }}
                                  >
                                    {isCheckExpanded ? '▼' : '▶'}
                                  </button>
                                </div>
                              </div>

                              {/* Show resources for this check */}
                              {isCheckExpanded && (
                                <div style={{
                                  marginLeft: '16px',
                                  marginTop: '4px',
                                  padding: '8px',
                                  backgroundColor: '#ffffff',
                                  border: '1px solid #e2e8f0',
                                  borderRadius: '4px'
                                }}>
                                  <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '4px', fontWeight: '600' }}>
                                    Affected Resources:
                                  </div>
                                  {checkFindings.slice(0, 5).map((finding, idx) => (
                                    <div
                                      key={idx}
                                      style={{
                                        fontSize: '10px',
                                        padding: '4px 6px',
                                        marginBottom: '2px',
                                        backgroundColor: '#fef2f2',
                                        borderLeft: '2px solid #ef4444',
                                        borderRadius: '2px'
                                      }}
                                    >
                                      <div style={{ color: '#1e293b', fontWeight: '500' }}>
                                        {finding.resource_type}
                                      </div>
                                      <div style={{
                                        color: '#64748b',
                                        fontFamily: 'monospace',
                                        fontSize: '9px',
                                        marginTop: '2px',
                                        wordBreak: 'break-all'
                                      }}>
                                        {finding.resource_id.substring(0, 60)}...
                                      </div>
                                      <div style={{ marginTop: '2px' }}>
                                        <span className="badge" style={{
                                          fontSize: '9px',
                                          padding: '2px 6px',
                                          backgroundColor: finding.severity === 'Critical' ? '#fee2e2' :
                                                         finding.severity === 'High' ? '#fed7aa' :
                                                         finding.severity === 'Medium' ? '#fef3c7' : '#dcfce7',
                                          color: finding.severity === 'Critical' ? '#991b1b' :
                                                 finding.severity === 'High' ? '#9a3412' :
                                                 finding.severity === 'Medium' ? '#854d0e' : '#166534'
                                        }}>
                                          {finding.severity}
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                                  {checkFindings.length > 5 && (
                                    <div style={{ fontSize: '10px', color: '#64748b', marginTop: '4px' }}>
                                      + {checkFindings.length - 5} more resources
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}

                        {/* Expand/Collapse checks button */}
                        {uniqueChecks.length > 3 && (
                          <button
                            onClick={() => toggleControlExpanded(control.control_id)}
                            style={{
                              fontSize: '11px',
                              color: '#3b82f6',
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              marginTop: '8px',
                              padding: '4px 8px',
                              textDecoration: 'underline',
                              fontWeight: '500'
                            }}
                          >
                            {isExpanded
                              ? '- Show less'
                              : `+ ${uniqueChecks.length - 3} more checks (${control.findings.length - uniqueChecks.slice(0, 3).reduce((sum, checkId) => sum + control.findings.filter(f => f.check_id === checkId).length, 0)} more findings)`}
                          </button>
                        )}
                      </div>

                      {/* View All Findings Button */}
                      <button
                        onClick={() => {
                          closeSidebar();
                          navigate(`/findings?framework=${encodeURIComponent(selectedFramework.framework)}`);
                        }}
                        className="btn btn-primary"
                        style={{
                          width: '100%',
                          marginTop: '12px',
                          fontSize: '11px',
                          padding: '8px 12px'
                        }}
                      >
                        View All {control.findings.length} Findings in Findings Page →
                      </button>
                    </div>
                  );
                })
              )}

              {!loadingControls && controls.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>✓</div>
                  <div style={{ fontSize: '16px', fontWeight: '500' }}>All Controls Passed</div>
                  <div style={{ fontSize: '14px', marginTop: '8px' }}>
                    No findings mapped to controls in this framework
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}

export default Frameworks;
