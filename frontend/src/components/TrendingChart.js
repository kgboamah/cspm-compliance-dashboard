/**
 * Risk Trending Chart Component - FINAL
 * Location: frontend/src/components/TrendingChart.js
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function TrendingChart({ accountId }) {
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (accountId) {
      fetchTrendData();
    }
  }, [accountId]);

  const fetchTrendData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('cspm_auth_token');
      
      const response = await axios.get(
        `http://localhost:8000/api/scores/account/${accountId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      let data = [];
      
      // Handle different response structures
      if (response.data && response.data.score_history && Array.isArray(response.data.score_history)) {
        data = response.data.score_history;
      } else if (response.data && response.data.scores && Array.isArray(response.data.scores)) {
        data = response.data.scores;
      }

      if (data.length < 2) {
        setTrendData([]);
        setLoading(false);
        return;
      }

      const chartData = data.map((entry) => {
        const point = {
          date: new Date(entry.created_at || entry.timestamp || Date.now()).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
          })
        };

        // Safely extract and round scores
        const cisScore = entry.cis_aws_score;
        const isoScore = entry.iso_27001_score;
        const nistScore = entry.nist_csf_score;
        const pciScore = entry.pci_dss_score;

        if (cisScore !== null && cisScore !== undefined) {
          point.cis_aws = Math.round(parseFloat(cisScore) * 10) / 10;
        }
        if (isoScore !== null && isoScore !== undefined) {
          point.iso_27001 = Math.round(parseFloat(isoScore) * 10) / 10;
        }
        if (nistScore !== null && nistScore !== undefined) {
          point.nist_csf = Math.round(parseFloat(nistScore) * 10) / 10;
        }
        if (pciScore !== null && pciScore !== undefined) {
          point.pci_dss = Math.round(parseFloat(pciScore) * 10) / 10;
        }

        // Calculate average safely
        const values = [cisScore, isoScore, nistScore, pciScore].filter(v => v !== null && v !== undefined);
        if (values.length > 0) {
          const avg = values.reduce((a, b) => a + parseFloat(b), 0) / values.length;
          point.average = Math.round(avg * 10) / 10;
        }

        return point;
      });

      setTrendData(chartData);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching trend data:', err);
      setTrendData([]);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 className="card-title">📈 Compliance Trend Analysis</h3>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!trendData || trendData.length < 2) {
    return (
      <div className="card" style={{ marginBottom: '20px', background: '#F0F9FF' }}>
        <h3 className="card-title">📈 Compliance Trend Analysis</h3>
        <div style={{ padding: '30px', textAlign: 'center', color: '#0369A1' }}>
          <p>Need at least 2 scans to display trends.</p>
          <p style={{ fontSize: '14px', color: '#0C4A6E' }}>Run additional scans to see compliance trending over time.</p>
        </div>
      </div>
    );
  }

  // Safe calculation of trend
  const firstPoint = trendData[0] || {};
  const lastPoint = trendData[trendData.length - 1] || {};
  
  let avgChange = 0;
  let trendDirection = '→';
  let trendColor = '#64748B';

  if (firstPoint.average && lastPoint.average) {
    avgChange = ((lastPoint.average - firstPoint.average) / firstPoint.average * 100).toFixed(1);
    trendDirection = avgChange > 0 ? '↑' : avgChange < 0 ? '↓' : '→';
    trendColor = avgChange > 0 ? '#16A34A' : avgChange < 0 ? '#DC2626' : '#64748B';
  }

  return (
    <div className="card" style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 className="card-title" style={{ margin: 0 }}>📈 Compliance Trend Analysis</h3>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '12px', color: '#64748B' }}>Overall Trend</div>
          <div style={{ 
            fontSize: '24px', 
            fontWeight: 'bold', 
            color: trendColor
          }}>
            {trendDirection} {avgChange}%
          </div>
        </div>
      </div>

      <div style={{
        background: '#F0F9FF',
        border: '1px solid #E0F2FE',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '20px',
        fontSize: '14px',
        color: '#0C4A6E'
      }}>
        <strong>📊 Insight:</strong> {
          avgChange > 0 
            ? `Compliance improving! Up ${avgChange}% since ${firstPoint.date || 'first scan'}.`
            : avgChange < 0
            ? `Compliance declining. Down ${Math.abs(avgChange)}% since ${firstPoint.date || 'first scan'}.`
            : `Compliance stable at ${lastPoint.average?.toFixed(1) || '—'}%.`
        }
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={trendData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis dataKey="date" stroke="#64748B" style={{ fontSize: '12px' }} />
          <YAxis domain={[0, 100]} stroke="#64748B" style={{ fontSize: '12px' }} />
          <Tooltip 
            contentStyle={{
              background: '#1E293B',
              border: '1px solid #475569',
              borderRadius: '8px',
              color: '#F1F5F9'
            }}
            formatter={(value) => value ? `${value.toFixed(1)}%` : 'N/A'}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          
          <Line type="monotone" dataKey="cis_aws" name="CIS AWS" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="iso_27001" name="ISO 27001" stroke="#10B981" strokeWidth={2} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="nist_csf" name="NIST CSF" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="pci_dss" name="PCI-DSS" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} />
          <Line 
            type="monotone" 
            dataKey="average" 
            name="Average" 
            stroke="#1E293B" 
            strokeWidth={3} 
            strokeDasharray="5 5"
            dot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendingChart;
