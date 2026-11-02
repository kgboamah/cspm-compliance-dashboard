import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function Trends() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [scans, setScans] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFramework, setSelectedFramework] = useState('All');
  const [frameworks, setFrameworks] = useState([]);

  useEffect(() => {
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchTrends(selectedAccount.id);
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
      }
    } catch (error) {
      console.error('Error fetching accounts:', error);
      setLoading(false);
    }
  };

  const fetchTrends = async (accountId) => {
    setLoading(true);
    try {
      // Get all scans for this account
      const scansResponse = await axios.get(
        `http://localhost:8000/api/scans/account/${accountId}`
      );
      const allScans = scansResponse.data.scans || [];

      // Filter only completed scans
      const completedScans = allScans.filter(s => s.scan_status === 'Completed');

      // Fetch scores for each completed scan
      const scanDataPromises = completedScans.map(async (scan) => {
        try {
          const scoresResponse = await axios.get(
            `http://localhost:8000/api/scores/scan/${scan.scan_id}`
          );
          
          if (scoresResponse.data.scores && scoresResponse.data.scores.length > 0) {
            return {
              scan_id: scan.scan_id,
              date: new Date(scan.completed_at).toLocaleDateString(),
              timestamp: new Date(scan.completed_at),
              scores: scoresResponse.data.scores
            };
          }
          return null;
        } catch (error) {
          console.error(`Error fetching scores for scan ${scan.scan_id}:`, error);
          return null;
        }
      });

      const scanData = (await Promise.all(scanDataPromises)).filter(d => d !== null);

      // Sort by timestamp (oldest first for trend)
      scanData.sort((a, b) => a.timestamp - b.timestamp);

      // Extract unique frameworks
      const frameworkSet = new Set();
      scanData.forEach(scan => {
        scan.scores.forEach(score => {
          frameworkSet.add(score.framework);
        });
      });

      setFrameworks(['All', ...Array.from(frameworkSet)]);
      setScans(scanData);
      prepareTrendData(scanData, 'All');
      setLoading(false);
    } catch (error) {
      console.error('Error fetching trends:', error);
      setLoading(false);
    }
  };

  const prepareTrendData = (scanData, framework) => {
    const data = scanData.map(scan => {
      const dataPoint = {
        date: scan.date,
        scan_id: scan.scan_id.substring(0, 8)
      };

      if (framework === 'All') {
        // Calculate average across all frameworks
        const avgScore = scan.scores.reduce((sum, s) => sum + s.overall_score, 0) / scan.scores.length;
        dataPoint['Average'] = parseFloat(avgScore.toFixed(1));

        // Add individual frameworks
        scan.scores.forEach(score => {
          dataPoint[score.framework] = parseFloat(score.overall_score.toFixed(1));
        });
      } else {
        // Single framework
        const score = scan.scores.find(s => s.framework === framework);
        if (score) {
          dataPoint[framework] = parseFloat(score.overall_score.toFixed(1));
        }
      }

      return dataPoint;
    });

    setTrendData(data);
  };

  const handleFrameworkChange = (framework) => {
    setSelectedFramework(framework);
    prepareTrendData(scans, framework);
  };

  const handleAccountChange = (e) => {
    const accountId = e.target.value;
    const account = accounts.find(a => a.id === accountId);
    setSelectedAccount(account);
    setSelectedFramework('All'); // Reset framework selection
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
          <h1>Compliance Trends</h1>
          <p>Track compliance scores over time</p>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📈</div>
          <h3>No Accounts Found</h3>
          <p>Add a cloud account to view compliance trends</p>
        </div>
      </div>
    );
  }

  if (scans.length === 0) {
    return (
      <div>
        <div className="page-header">
          <h1>Compliance Trends</h1>
          <p>Track compliance scores over time</p>
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
          <div className="empty-state-icon">📈</div>
          <h3>Not Enough Data for {selectedAccount.account_name}</h3>
          <p>Run multiple scans to see trends over time</p>
        </div>
      </div>
    );
  }

  const colors = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6'];

  // Calculate trend direction
  const calculateTrend = () => {
    if (scans.length < 2) return { direction: 'neutral', percentage: 0 };
    
    const firstAvg = scans[0].scores.reduce((sum, s) => sum + s.overall_score, 0) / scans[0].scores.length;
    const lastAvg = scans[scans.length - 1].scores.reduce((sum, s) => sum + s.overall_score, 0) / scans[scans.length - 1].scores.length;
    const change = lastAvg - firstAvg;
    
    return {
      direction: change > 0 ? 'improving' : change < 0 ? 'declining' : 'stable',
      percentage: change
    };
  };

  const trend = calculateTrend();

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Compliance Trends</h1>
          <p>Historical view of compliance scores across scans</p>
        </div>
        
        {/* Trend Indicator */}
        {scans.length >= 2 && (
          <div style={{
            padding: '12px 20px',
            borderRadius: '8px',
            backgroundColor: trend.direction === 'improving' ? '#dcfce7' : 
                           trend.direction === 'declining' ? '#fee2e2' : '#f1f5f9',
            border: `2px solid ${trend.direction === 'improving' ? '#22c55e' : 
                                trend.direction === 'declining' ? '#ef4444' : '#94a3b8'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <span style={{ fontSize: '24px' }}>
              {trend.direction === 'improving' ? '📈' : 
               trend.direction === 'declining' ? '📉' : '➡️'}
            </span>
            <div>
              <strong style={{
                color: trend.direction === 'improving' ? '#15803d' : 
                       trend.direction === 'declining' ? '#991b1b' : '#475569'
              }}>
                {trend.direction === 'improving' ? 'Improving Trend' : 
                 trend.direction === 'declining' ? 'Declining Trend' : 'Stable Trend'}
              </strong>
              <p style={{ margin: '4px 0 0 0', fontSize: '14px' }}>
                {trend.percentage >= 0 ? '+' : ''}{trend.percentage.toFixed(1)}% change over {scans.length} scans
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
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
            <label>Framework</label>
            <select
              value={selectedFramework}
              onChange={(e) => handleFrameworkChange(e.target.value)}
            >
              {frameworks.map(fw => (
                <option key={fw} value={fw}>{fw}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            {selectedAccount.account_name} - {selectedFramework === 'All' ? 'All Frameworks' : selectedFramework}
          </h3>
          <span style={{
            padding: '6px 12px',
            borderRadius: '6px',
            backgroundColor: '#f1f5f9',
            fontSize: '14px',
            fontWeight: '600',
            color: '#475569'
          }}>
            {scans.length} scans analyzed
          </span>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              angle={-45}
              textAnchor="end"
              height={100}
            />
            <YAxis
              domain={[0, 100]}
              label={{ value: 'Compliance Score (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip />
            <Legend />
            {selectedFramework === 'All' ? (
              <>
                <Line
                  type="monotone"
                  dataKey="Average"
                  stroke="#1e293b"
                  strokeWidth={3}
                  dot={{ r: 6 }}
                  name="Average"
                />
                {frameworks.slice(1).map((fw, idx) => (
                  <Line
                    key={fw}
                    type="monotone"
                    dataKey={fw}
                    stroke={colors[idx % colors.length]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name={fw}
                  />
                ))}
              </>
            ) : (
              <Line
                type="monotone"
                dataKey={selectedFramework}
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ r: 6 }}
                name={selectedFramework}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Scans Analyzed</div>
          <div className="stat-value">{scans.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Latest Score</div>
          <div className="stat-value">
            {selectedFramework === 'All' ? (
              <>
                {(scans[scans.length - 1].scores.reduce((sum, s) => sum + s.overall_score, 0) /
                  scans[scans.length - 1].scores.length).toFixed(0)}%
              </>
            ) : (
              <>
                {(() => {
                  const score = scans[scans.length - 1].scores.find(s => s.framework === selectedFramework);
                  return score ? `${score.overall_score.toFixed(0)}%` : 'N/A';
                })()}
              </>
            )}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Change from First Scan</div>
          <div className="stat-value">
            {(() => {
              if (selectedFramework === 'All') {
                const firstAvg = scans[0].scores.reduce((sum, s) => sum + s.overall_score, 0) / scans[0].scores.length;
                const lastAvg = scans[scans.length - 1].scores.reduce((sum, s) => sum + s.overall_score, 0) /
                                scans[scans.length - 1].scores.length;
                const change = lastAvg - firstAvg;
                return (
                  <span style={{ color: change >= 0 ? '#22c55e' : '#ef4444' }}>
                    {change >= 0 ? '+' : ''}{change.toFixed(1)}%
                  </span>
                );
              } else {
                const firstScore = scans[0].scores.find(s => s.framework === selectedFramework);
                const lastScore = scans[scans.length - 1].scores.find(s => s.framework === selectedFramework);
                if (firstScore && lastScore) {
                  const change = lastScore.overall_score - firstScore.overall_score;
                  return (
                    <span style={{ color: change >= 0 ? '#22c55e' : '#ef4444' }}>
                      {change >= 0 ? '+' : ''}{change.toFixed(1)}%
                    </span>
                  );
                }
                return 'N/A';
              }
            })()}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Frameworks Tracked</div>
          <div className="stat-value">{frameworks.length - 1}</div>
        </div>
      </div>

      {/* Scan Details Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Scan History</h3>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Scan ID</th>
                {selectedFramework === 'All' ? (
                  <>
                    <th>Average Score</th>
                    {frameworks.slice(1).map(fw => (
                      <th key={fw}>{fw}</th>
                    ))}
                  </>
                ) : (
                  <th>{selectedFramework} Score</th>
                )}
              </tr>
            </thead>
            <tbody>
              {scans.map((scan, idx) => (
                <tr key={idx}>
                  <td>{scan.date}</td>
                  <td>
                    <code>{scan.scan_id.substring(0, 8)}...</code>
                  </td>
                  {selectedFramework === 'All' ? (
                    <>
                      <td>
                        <strong>
                          {(scan.scores.reduce((sum, s) => sum + s.overall_score, 0) / scan.scores.length).toFixed(1)}%
                        </strong>
                      </td>
                      {frameworks.slice(1).map(fw => {
                        const score = scan.scores.find(s => s.framework === fw);
                        return (
                          <td key={fw}>
                            {score ? (
                              <span style={{
                                color: score.overall_score > 80 ? '#22c55e' :
                                       score.overall_score > 50 ? '#f59e0b' : '#ef4444'
                              }}>
                                {score.overall_score.toFixed(1)}%
                              </span>
                            ) : '-'}
                          </td>
                        );
                      })}
                    </>
                  ) : (
                    <td>
                      {(() => {
                        const score = scan.scores.find(s => s.framework === selectedFramework);
                        return score ? (
                          <strong style={{
                            color: score.overall_score > 80 ? '#22c55e' :
                                   score.overall_score > 50 ? '#f59e0b' : '#ef4444'
                          }}>
                            {score.overall_score.toFixed(1)}%
                          </strong>
                        ) : '-';
                      })()}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Trends;
