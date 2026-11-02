/**
 * Toxic Combinations / Critical Risk Paths Component
 * Location: frontend/src/components/ToxicCombinations.js
 * 
 * Displays detected attack paths from correlated security findings
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ToxicCombinations({ accountId }) {
  const [combinations, setCombinations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedPath, setExpandedPath] = useState(null);

  useEffect(() => {
    if (accountId) {
      fetchToxicCombinations();
    }
  }, [accountId]);

  const fetchToxicCombinations = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `http://localhost:8000/api/scores/account/${accountId}/toxic-combinations`
      );
      
      setCombinations(response.data.combinations || []);
      setSummary(response.data.summary || {});
      setLoading(false);
    } catch (err) {
      console.error('Error fetching toxic combinations:', err);
      setError('Failed to load risk paths');
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': '#DC2626',
      'HIGH': '#EA580C',
      'MEDIUM': '#CA8A04',
      'LOW': '#16A34A'
    };
    return colors[severity] || '#64748B';
  };

  const getRiskScoreColor = (score) => {
    if (score >= 90) return '#DC2626'; // Critical
    if (score >= 75) return '#EA580C'; // High
    if (score >= 50) return '#CA8A04'; // Medium
    return '#16A34A'; // Low
  };

  if (loading) {
    return (
      <div className="card">
        <h3 className="card-title">🎯 Critical Risk Paths</h3>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3 className="card-title">🎯 Critical Risk Paths</h3>
        <div style={{ padding: '20px', color: '#DC2626', textAlign: 'center' }}>
          {error}
        </div>
      </div>
    );
  }

  if (!combinations || combinations.length === 0) {
    return (
      <div className="card" style={{ background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)', color: 'white' }}>
        <h3 className="card-title" style={{ color: 'white' }}>🎯 Critical Risk Paths</h3>
        <div style={{ textAlign: 'center', padding: '30px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
          <h3 style={{ margin: '0 0 8px 0', color: 'white' }}>No Critical Attack Paths Detected</h3>
          <p style={{ margin: 0, opacity: 0.9 }}>
            Your security findings do not currently combine into high-risk attack scenarios.
            Continue monitoring for emerging threats.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ background: 'linear-gradient(135deg, #DC2626 0%, #991B1B 100%)', color: 'white' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 className="card-title" style={{ color: 'white', margin: 0 }}>
          🎯 Critical Risk Paths Detected
        </h3>
        <div style={{ 
          background: 'rgba(255, 255, 255, 0.2)', 
          padding: '8px 16px', 
          borderRadius: '20px',
          fontSize: '14px',
          fontWeight: 'bold'
        }}>
          {summary.total_combinations} Attack Path{summary.total_combinations !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', 
        gap: '12px',
        marginBottom: '24px'
      }}>
        <div style={{ background: 'rgba(255, 255, 255, 0.15)', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', opacity: 0.9, marginBottom: '4px' }}>Highest Risk Score</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{summary.highest_risk_score}</div>
        </div>
        
        <div style={{ background: 'rgba(255, 255, 255, 0.15)', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', opacity: 0.9, marginBottom: '4px' }}>Critical Paths</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{summary.critical_combinations}</div>
        </div>
        
        <div style={{ background: 'rgba(255, 255, 255, 0.15)', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', opacity: 0.9, marginBottom: '4px' }}>High Risk Paths</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{summary.high_combinations}</div>
        </div>
        
        <div style={{ background: 'rgba(255, 255, 255, 0.15)', padding: '16px', borderRadius: '8px' }}>
          <div style={{ fontSize: '12px', opacity: 0.9, marginBottom: '4px' }}>Immediate Action</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{summary.requires_immediate_action}</div>
        </div>
      </div>

      {/* Risk Paths */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {combinations.map((combo, idx) => (
          <div 
            key={idx}
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              borderRadius: '12px',
              padding: '20px',
              color: '#1E293B',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <h4 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold', color: '#1E293B' }}>
                    {combo.name}
                  </h4>
                  <span 
                    className="badge"
                    style={{ 
                      backgroundColor: getSeverityColor(combo.severity),
                      color: 'white',
                      fontSize: '11px',
                      padding: '4px 10px'
                    }}
                  >
                    {combo.severity}
                  </span>
                </div>
                <p style={{ margin: '0 0 8px 0', color: '#64748B', fontSize: '14px' }}>
                  {combo.description}
                </p>
                <div style={{ fontSize: '13px', color: '#0891B2', fontWeight: '500' }}>
                  ⏰ {combo.mitigation_priority}
                </div>
              </div>
              
              <div style={{
                background: getRiskScoreColor(combo.risk_score),
                color: 'white',
                padding: '12px',
                borderRadius: '8px',
                textAlign: 'center',
                minWidth: '80px'
              }}>
                <div style={{ fontSize: '12px', opacity: 0.9 }}>Risk Score</div>
                <div style={{ fontSize: '32px', fontWeight: 'bold', lineHeight: '1' }}>{combo.risk_score}</div>
              </div>
            </div>

            {/* Matched Findings */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ 
                fontSize: '13px', 
                fontWeight: '600', 
                color: '#64748B', 
                marginBottom: '8px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Correlated Findings ({combo.matched_findings.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {combo.matched_findings.map((finding, findingIdx) => (
                  <div 
                    key={findingIdx}
                    style={{
                      background: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                      borderRadius: '6px',
                      padding: '12px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '500', fontSize: '14px', marginBottom: '4px' }}>
                        {finding.check_name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748B' }}>
                        {finding.resource_type} {finding.resource_id ? `• ${finding.resource_id.substring(0, 40)}...` : ''}
                      </div>
                    </div>
                    <span 
                      className={`badge ${finding.severity.toLowerCase()}`}
                      style={{ marginLeft: '12px' }}
                    >
                      {finding.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Attack Path */}
            <div>
              <button
                onClick={() => setExpandedPath(expandedPath === idx ? null : idx)}
                style={{
                  width: '100%',
                  background: '#0891B2',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '10px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                {expandedPath === idx ? '▼' : '▶'} View Attack Path
              </button>
              
              {expandedPath === idx && (
                <div style={{ 
                  marginTop: '12px', 
                  background: '#FEF3C7', 
                  border: '2px solid #F59E0B',
                  borderRadius: '8px', 
                  padding: '16px' 
                }}>
                  <div style={{ 
                    fontSize: '13px', 
                    fontWeight: '600', 
                    color: '#92400E', 
                    marginBottom: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    ⚠️ POTENTIAL ATTACK CHAIN
                  </div>
                  <ol style={{ margin: 0, paddingLeft: '20px', color: '#92400E' }}>
                    {combo.attack_path.map((step, stepIdx) => (
                      <li key={stepIdx} style={{ marginBottom: '8px', fontSize: '14px' }}>
                        <strong>Step {stepIdx + 1}:</strong> {step}
                      </li>
                    ))}
                  </ol>
                  <div style={{ 
                    marginTop: '12px', 
                    padding: '12px', 
                    background: 'white', 
                    borderRadius: '6px',
                    fontSize: '13px',
                    color: '#92400E'
                  }}>
                    <strong>🎯 Impact:</strong> This combination of vulnerabilities creates a complete attack path 
                    that could lead to unauthorized access, data exfiltration, or system compromise without detection.
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Footer CTA */}
      <div style={{ 
        marginTop: '20px', 
        padding: '16px', 
        background: 'rgba(255, 255, 255, 0.15)', 
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '14px', marginBottom: '8px' }}>
          <strong>⚡ Immediate Action Required</strong>
        </div>
        <div style={{ fontSize: '13px', opacity: 0.9 }}>
          These risk paths represent critical security gaps. Remediate correlated findings to break the attack chain.
        </div>
      </div>
    </div>
  );
}

export default ToxicCombinations;
