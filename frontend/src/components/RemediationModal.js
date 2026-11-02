/**
 * Remediation Modal Component
 * Location: frontend/src/components/RemediationModal.js
 * 
 * Shows remediation guidance for security findings
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function RemediationModal({ findingId, onClose }) {
  const [remediation, setRemediation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('steps');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchRemediation();
  }, [findingId]);

  const fetchRemediation = async () => {
    try {
      const token = localStorage.getItem('cspm_auth_token');
      const response = await axios.get(
        `http://localhost:8000/api/scores/finding/${findingId}/remediation`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setRemediation(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching remediation:', error);
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': '#dc2626',
      'HIGH': '#ea580c',
      'MEDIUM': '#f59e0b',
      'LOW': '#84cc16'
    };
    return colors[severity] || '#64748b';
  };

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '800px' }}>
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <div className="spinner"></div>
            <p style={{ marginTop: '16px', color: '#64748b' }}>Loading remediation guidance...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!remediation) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
          <div style={{ padding: '24px' }}>
            <h2>Remediation Not Available</h2>
            <p>Unable to load remediation guidance for this finding.</p>
            <button onClick={onClose} className="btn btn-secondary" style={{ marginTop: '16px' }}>Close</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', maxHeight: '90vh', overflow: 'auto' }}>
        {/* Header */}
        <div style={{ padding: '24px', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, backgroundColor: 'white', zIndex: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <h2 style={{ margin: 0, fontSize: '20px', color: '#1e293b' }}>🔧 Remediation Guidance</h2>
                <span style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: '600',
                  backgroundColor: getSeverityColor(remediation.severity) + '20',
                  color: getSeverityColor(remediation.severity)
                }}>
                  {remediation.severity}
                </span>
              </div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '16px', color: '#475569' }}>{remediation.title}</h3>
              <div style={{ fontSize: '13px', color: '#64748b' }}>
                <strong>Resource:</strong> {remediation.resource_id} ({remediation.resource_type})
              </div>
            </div>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#64748b',
                padding: '0',
                marginLeft: '16px'
              }}
            >
              ×
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ borderBottom: '1px solid #e2e8f0', padding: '0 24px', backgroundColor: '#f8fafc' }}>
          <div style={{ display: 'flex', gap: '0' }}>
            {['steps', 'aws-cli', 'terraform', 'impact'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: '12px 20px',
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: activeTab === tab ? '#3b82f6' : '#64748b',
                  borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
                  transition: 'all 0.2s'
                }}
              >
                {tab === 'steps' && '📋 Steps'}
                {tab === 'aws-cli' && '💻 AWS CLI'}
                {tab === 'terraform' && '🏗️ Terraform'}
                {tab === 'impact' && '⚠️ Impact & Prevention'}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '24px' }}>
          {/* Steps Tab */}
          {activeTab === 'steps' && (
            <div>
              <p style={{ fontSize: '14px', color: '#475569', marginBottom: '20px' }}>
                {remediation.description}
              </p>
              <h4 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '12px', color: '#1e293b' }}>
                Remediation Steps:
              </h4>
              <ol style={{ paddingLeft: '20px', margin: 0 }}>
                {remediation.remediation_steps.map((step, index) => (
                  <li key={index} style={{ marginBottom: '8px', fontSize: '14px', color: '#475569' }}>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* AWS CLI Tab */}
          {activeTab === 'aws-cli' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: '600', margin: 0, color: '#1e293b' }}>
                  AWS CLI Command:
                </h4>
                <button
                  onClick={() => copyToClipboard(remediation.aws_cli)}
                  className="btn btn-secondary"
                  style={{ fontSize: '13px', padding: '6px 12px' }}
                >
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
              </div>
              <pre style={{
                backgroundColor: '#1e293b',
                color: '#e2e8f0',
                padding: '16px',
                borderRadius: '6px',
                fontSize: '13px',
                overflow: 'auto',
                fontFamily: 'monospace',
                lineHeight: '1.6'
              }}>
                {remediation.aws_cli}
              </pre>
              <div style={{
                marginTop: '12px',
                padding: '12px',
                backgroundColor: '#fef3c7',
                borderLeft: '4px solid #f59e0b',
                borderRadius: '4px',
                fontSize: '13px',
                color: '#92400e'
              }}>
                <strong>⚠️ Note:</strong> Review and customize the command for your environment before execution.
                Test in a non-production environment first.
              </div>
            </div>
          )}

          {/* Terraform Tab */}
          {activeTab === 'terraform' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: '600', margin: 0, color: '#1e293b' }}>
                  Terraform Configuration:
                </h4>
                <button
                  onClick={() => copyToClipboard(remediation.terraform)}
                  className="btn btn-secondary"
                  style={{ fontSize: '13px', padding: '6px 12px' }}
                >
                  {copied ? '✓ Copied!' : '📋 Copy'}
                </button>
              </div>
              <pre style={{
                backgroundColor: '#1e293b',
                color: '#e2e8f0',
                padding: '16px',
                borderRadius: '6px',
                fontSize: '13px',
                overflow: 'auto',
                fontFamily: 'monospace',
                lineHeight: '1.6'
              }}>
                {remediation.terraform}
              </pre>
              <div style={{
                marginTop: '12px',
                padding: '12px',
                backgroundColor: '#dbeafe',
                borderLeft: '4px solid #3b82f6',
                borderRadius: '4px',
                fontSize: '13px',
                color: '#1e40af'
              }}>
                <strong>💡 Tip:</strong> Add this configuration to your Infrastructure as Code repository
                and apply via your standard deployment pipeline.
              </div>
            </div>
          )}

          {/* Impact & Prevention Tab */}
          {activeTab === 'impact' && (
            <div>
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '8px', color: '#1e293b' }}>
                  Security Impact:
                </h4>
                <p style={{ fontSize: '14px', color: '#475569', margin: 0 }}>
                  {remediation.impact}
                </p>
              </div>
              <div>
                <h4 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '8px', color: '#1e293b' }}>
                  Prevention Strategy:
                </h4>
                <p style={{ fontSize: '14px', color: '#475569', margin: 0 }}>
                  {remediation.prevention}
                </p>
              </div>
              <div style={{
                marginTop: '20px',
                padding: '16px',
                backgroundColor: '#f0fdf4',
                borderLeft: '4px solid #22c55e',
                borderRadius: '4px'
              }}>
                <strong style={{ color: '#166534', fontSize: '14px' }}>🎯 Best Practice:</strong>
                <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#166534' }}>
                  Implement security controls at the infrastructure level using Infrastructure as Code (IaC)
                  and enforce policies with AWS Service Control Policies (SCPs) or Azure Policy.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid #e2e8f0', backgroundColor: '#f8fafc', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn btn-primary">
            Done
          </button>
        </div>

        <style>{`
          .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 20px;
          }
          .modal-content {
            background: white;
            border-radius: 8px;
            width: 100%;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            animation: slideIn 0.2s ease-out;
          }
          @keyframes slideIn {
            from {
              transform: translateY(-20px);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }
        `}</style>
      </div>
    </div>
  );
}

export default RemediationModal;
