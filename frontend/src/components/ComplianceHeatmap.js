import React, { useState, useEffect } from 'react';

function ComplianceHeatmap({ accounts }) {
  const [heatmapData, setHeatmapData] = useState([]);
  const [loading, setLoading] = useState(true);

  const frameworks = ['CIS AWS', 'ISO 27001', 'NIST CSF', 'PCI-DSS'];

  useEffect(() => {
    fetchHeatmapData();
  }, [accounts]);

  const fetchHeatmapData = async () => {
    try {
      setLoading(true);
      const data = await Promise.all(
        accounts.map(async (account) => {
          try {
            const response = await fetch(
              `http://localhost:8000/api/scores/account/${account.id}`
            );
            const scoresData = await response.json();
            const scoresMap = {};
            
            if (scoresData.scores && scoresData.scores.length > 0) {
              scoresData.scores.forEach(score => {
                const rate = score.total_controls > 0
                  ? (score.controls_passed / score.total_controls) * 100
                  : 0;
                scoresMap[score.framework] = parseFloat(rate.toFixed(1));
              });
            }

            return {
              accountId: account.id,
              accountName: account.account_name,
              scores: scoresMap
            };
          } catch (err) {
            console.error(`Error fetching scores for ${account.account_name}:`, err);
            return {
              accountId: account.id,
              accountName: account.account_name,
              scores: {}
            };
          }
        })
      );

      setHeatmapData(data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching heatmap data:', err);
      setLoading(false);
    }
  };

  const getHeatmapColor = (score) => {
    if (score === null || score === undefined) return '#e5e7eb';
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#f59e0b';
    if (score >= 40) return '#eab308';
    return '#ef4444';
  };

  const getTextColor = (score) => {
    if (score >= 40) return 'white';
    return 'white';
  };

  if (loading) {
    return (
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 className="card-title">Compliance Heatmap</h3>
        <div style={{ textAlign: 'center', padding: '20px', color: '#94a3b8' }}>
          Loading heatmap data...
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ marginBottom: '20px' }}>
      <div className="card-header">
        <h3 className="card-title">📊 Compliance Heatmap - All Accounts</h3>
        <p style={{ margin: '8px 0 0 0', fontSize: '14px', color: '#64748b' }}>
          Compliance score (%) for each account across all frameworks
        </p>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <div style={{ minWidth: '900px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '200px repeat(4, 1fr)', gap: '2px', marginBottom: '8px' }}>
            <div style={{ 
              padding: '12px', 
              fontWeight: '600',
              fontSize: '14px',
              color: '#64748b'
            }}>
              Account
            </div>
            {frameworks.map(framework => (
              <div
                key={framework}
                style={{
                  padding: '12px',
                  fontWeight: '600',
                  fontSize: '13px',
                  color: '#64748b',
                  textAlign: 'center',
                  borderBottom: '2px solid #e2e8f0'
                }}
              >
                {framework}
              </div>
            ))}
          </div>

          {heatmapData.map((row) => (
            <div
              key={row.accountId}
              style={{
                display: 'grid',
                gridTemplateColumns: '200px repeat(4, 1fr)',
                gap: '2px',
                marginBottom: '8px'
              }}
            >
              <div style={{
                padding: '12px',
                fontSize: '14px',
                fontWeight: '500',
                color: '#1e293b',
                borderRight: '2px solid #e2e8f0',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {row.accountName}
              </div>

              {frameworks.map(framework => {
                const score = row.scores[framework];
                const color = getHeatmapColor(score);
                const textColor = getTextColor(score);

                return (
                  <div
                    key={`${row.accountId}-${framework}`}
                    style={{
                      padding: '12px',
                      backgroundColor: color,
                      color: textColor,
                      textAlign: 'center',
                      fontWeight: '600',
                      fontSize: '14px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'scale(1.05)';
                      e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                      e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
                    }}
                    title={score !== null && score !== undefined ? `${score}% compliant` : 'No data'}
                  >
                    {score !== null && score !== undefined ? `${score}%` : '—'}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div style={{
        display: 'flex',
        gap: '20px',
        marginTop: '20px',
        padding: '16px 0',
        borderTop: '1px solid #e2e8f0',
        fontSize: '13px',
        color: '#64748b',
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '24px', height: '24px', backgroundColor: '#22c55e', borderRadius: '4px' }}></div>
          <span>Excellent (≥80%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '24px', height: '24px', backgroundColor: '#f59e0b', borderRadius: '4px' }}></div>
          <span>Good (60-79%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '24px', height: '24px', backgroundColor: '#eab308', borderRadius: '4px' }}></div>
          <span>Fair (40-59%)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '24px', height: '24px', backgroundColor: '#ef4444', borderRadius: '4px' }}></div>
          <span>Poor (&lt;40%)</span>
        </div>
      </div>
    </div>
  );
}

export default ComplianceHeatmap;
