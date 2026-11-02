/**
 * Executive Summary Cards Component
 * Location: frontend/src/components/ExecutiveSummaryCards.js
 * 
 * Uses ONLY existing endpoints:
 * - GET /api/scores/account/{account_id}
 * - GET /api/scores/scan/{scan_id}/findings
 * - GET /api/scores/account/{account_id}/recurring-findings
 * - GET /api/scores/account/{account_id}/toxic-combinations
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ExecutiveSummaryCards({ accountId, selectedAccount }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (accountId) {
      fetchSummaryData();
    }
  }, [accountId]);

  const fetchSummaryData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('cspm_auth_token');

      // Fetch compliance scores for account
      const scoresResponse = await axios.get(
        `http://localhost:8000/api/scores/account/${accountId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const scores = scoresResponse.data.scores || [];

      const avgComplianceScore = scores.length > 0 
        ? (scores.reduce((sum, s) => sum + parseFloat(s.overall_score || 0), 0) / scores.length).toFixed(1)
        : 0;

      // Fetch recurring findings
      const recurringResponse = await axios.get(
        `http://localhost:8000/api/scores/account/${accountId}/recurring-findings`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const recurring = recurringResponse.data.recurring_findings || [];

      // Count findings that FAIL in 2+ scans (truly problematic)
      const trulyRecurring = recurring.filter(r => {
        const failCount = (r.status_history || []).filter(s => s.status === 'Fail').length;
        return failCount >= 2;  // Only count if failed in 2+ scans
      });

      const recurringCount = trulyRecurring.length;
      const daysPersistent = trulyRecurring.length > 0
        ? Math.max(...trulyRecurring.map(r => {
            const firstSeen = new Date(r.first_seen);
            const lastSeen = new Date(r.last_seen);
            return Math.floor((lastSeen - firstSeen) / (1000 * 60 * 60 * 24));
          }))
        : 0;
        
      // Fetch toxic combinations
      const toxicResponse = await axios.get(
        `http://localhost:8000/api/scores/account/${accountId}/toxic-combinations`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const summary_data = toxicResponse.data.summary || {};
      const combinations = toxicResponse.data.combinations || [];

      const criticalCount = summary_data.critical_combinations || 0;
      const highCount = summary_data.high_combinations || 0;
      const mediumCount = summary_data.medium_combinations || 0;
      const totalFindings = summary_data.total_combinations ? 
        (criticalCount + highCount + mediumCount) : 0;

      const immediateActionItems = combinations.filter(c => 
        c.mitigation_priority && c.mitigation_priority.includes('IMMEDIATE')
      ).length;

      setSummary({
        criticalFindings: criticalCount,
        highFindings: highCount,
        mediumFindings: mediumCount,
        totalFindings: summary_data.total_combinations || 0,
        avgComplianceScore,
        recurringCount,
        daysPersistent,
        immediateActionItems,
        toxicCombinationsCount: summary_data.total_combinations || 0,
        highestRiskScore: summary_data.highest_risk_score || 0,
        accountName: selectedAccount?.account_name || 'Unknown Account'
      });

      setLoading(false);
    } catch (err) {
      console.error('Error fetching summary data:', err);
      setSummary({
        criticalFindings: 0,
        highFindings: 0,
        mediumFindings: 0,
        totalFindings: 0,
        avgComplianceScore: 0,
        recurringCount: 0,
        daysPersistent: 0,
        immediateActionItems: 0,
        toxicCombinationsCount: 0,
        highestRiskScore: 0,
        accountName: selectedAccount?.account_name || 'Unknown Account'
      });
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ marginBottom: '20px', color: '#1E293B', fontSize: '24px', fontWeight: 'bold' }}>
          Executive Summary
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} style={{ height: '180px', background: '#F1F5F9', borderRadius: '12px', padding: '20px' }}>
              <div className="spinner" style={{ marginTop: '60px' }}></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  const getCriticalStyle = (count) => {
    if (count === 0) return { background: '#ECFDF5', borderLeft: '4px solid #10B981' };
    if (count < 5) return { background: '#FEF3C7', borderLeft: '4px solid #F59E0B' };
    return { background: '#FEE2E2', borderLeft: '4px solid #EF4444' };
  };

  const getComplianceStyle = (score) => {
    score = parseFloat(score);
    if (score >= 80) return { background: '#ECFDF5', borderLeft: '4px solid #10B981' };
    if (score >= 60) return { background: '#FEF3C7', borderLeft: '4px solid #F59E0B' };
    return { background: '#FEE2E2', borderLeft: '4px solid #EF4444' };
  };

  const getRecurringStyle = (count) => {
    if (count === 0) return { background: '#ECFDF5', borderLeft: '4px solid #10B981' };
    if (count < 3) return { background: '#FEF3C7', borderLeft: '4px solid #F59E0B' };
    return { background: '#FEE2E2', borderLeft: '4px solid #EF4444' };
  };

  const getActionStyle = (count) => {
    if (count === 0) return { background: '#ECFDF5', borderLeft: '4px solid #10B981' };
    if (count < 3) return { background: '#FEF3C7', borderLeft: '4px solid #F59E0B' };
    return { background: '#FEE2E2', borderLeft: '4px solid #EF4444' };
  };

  return (
    <div style={{ marginBottom: '30px' }}>
      <h2 style={{ marginBottom: '20px', color: '#1E293B', fontSize: '24px', fontWeight: 'bold' }}>
        📊 Executive Summary - {summary.accountName}
      </h2>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
        gap: '20px',
        marginBottom: '30px'
      }}>
        {/* Card 1: Critical Issues */}
        <div style={{
          ...getCriticalStyle(summary.criticalFindings),
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          transition: 'transform 0.2s, box-shadow 0.2s',
          cursor: 'pointer'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🚨</div>
          <h3 style={{ margin: '0 0 12px 0', color: '#1E293B', fontSize: '14px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Attack Paths Detected
          </h3>
          <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#EF4444', margin: '8px 0' }}>
            {summary.toxicCombinationsCount}
          </div>
          <p style={{ margin: '12px 0 0 0', fontSize: '13px', color: '#64748B' }}>
            Require immediate action
          </p>
          <div style={{ marginTop: '12px', fontSize: '12px', color: '#0C4A6E', fontWeight: '600' }}>
            {summary.immediateActionItems} Immediate | Max Risk: {summary.highestRiskScore}
          </div>
        </div>

        {/* Card 2: Compliance Score */}
        <div style={{
          ...getComplianceStyle(summary.avgComplianceScore),
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          transition: 'transform 0.2s, box-shadow 0.2s',
          cursor: 'pointer'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>📈</div>
          <h3 style={{ margin: '0 0 12px 0', color: '#1E293B', fontSize: '14px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Compliance Score
          </h3>
          <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#3B82F6', margin: '8px 0' }}>
            {summary.avgComplianceScore}%
          </div>
          <p style={{ margin: '12px 0 0 0', fontSize: '13px', color: '#64748B' }}>
            Average across all frameworks
          </p>
          <div style={{ 
            marginTop: '12px', 
            fontSize: '12px', 
            fontWeight: '600',
            color: summary.avgComplianceScore >= 80 ? '#10B981' : summary.avgComplianceScore >= 60 ? '#F59E0B' : '#EF4444'
          }}>
            {summary.avgComplianceScore >= 80 ? '✓ Strong' : summary.avgComplianceScore >= 60 ? '⚠ Fair' : '✗ Poor'}
          </div>
        </div>

        {/* Card 3: Recurring Problems */}
        <div style={{
          ...getRecurringStyle(summary.recurringCount),
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          transition: 'transform 0.2s, box-shadow 0.2s',
          cursor: 'pointer'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🔄</div>
          <h3 style={{ margin: '0 0 12px 0', color: '#1E293B', fontSize: '14px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Recurring Problems
          </h3>
          <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#F59E0B', margin: '8px 0' }}>
            {summary.recurringCount}
          </div>
          <p style={{ margin: '12px 0 0 0', fontSize: '13px', color: '#64748B' }}>
            Issues persisting across scans
          </p>
          <div style={{ marginTop: '12px', fontSize: '12px', color: '#0C4A6E', fontWeight: '600' }}>
            Up to {summary.daysPersistent} days unresolved
          </div>
        </div>

        {/* Card 4: Immediate Action Items */}
        <div style={{
          ...getActionStyle(summary.immediateActionItems),
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          transition: 'transform 0.2s, box-shadow 0.2s',
          cursor: 'pointer'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>⚡</div>
          <h3 style={{ margin: '0 0 12px 0', color: '#1E293B', fontSize: '14px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Critical Issues
          </h3>
          <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#DC2626', margin: '8px 0' }}>
            {summary.criticalFindings}
          </div>
          <p style={{ margin: '12px 0 0 0', fontSize: '13px', color: '#64748B' }}>
            Critical severity findings
          </p>
          <div style={{ marginTop: '12px', fontSize: '12px', color: '#0C4A6E', fontWeight: '600' }}>
            {summary.highFindings} High | {summary.mediumFindings} Medium
          </div>
        </div>
      </div>

      {/* Risk Assessment */}
      <div style={{
        background: '#F8FAFC',
        borderRadius: '12px',
        padding: '20px',
        border: '1px solid #E2E8F0',
        marginTop: '20px'
      }}>
        <h4 style={{ margin: '0 0 12px 0', color: '#1E293B', fontSize: '14px', fontWeight: '600' }}>
          🎯 Risk Assessment Summary
        </h4>
        
        <div style={{
          marginTop: '16px',
          padding: '12px',
          background: summary.criticalFindings > 0 || summary.immediateActionItems > 0 ? '#FEE2E2' : '#ECFDF5',
          borderRadius: '8px',
          fontSize: '13px',
          color: summary.criticalFindings > 0 || summary.immediateActionItems > 0 ? '#7F1D1D' : '#065F46',
          fontWeight: '500'
        }}>
          {summary.criticalFindings > 0
            ? `⚠️ ${summary.criticalFindings} critical issue(s) and ${summary.immediateActionItems} immediate action item(s) detected. Urgent remediation required to prevent potential breach.`
            : summary.immediateActionItems > 0
            ? `⚠️ ${summary.immediateActionItems} attack path(s) requiring immediate remediation. Review Toxic Combinations for details.`
            : '✓ No critical issues detected. Continue monitoring for compliance.'}
        </div>
      </div>
    </div>
  );
}

export default ExecutiveSummaryCards;
