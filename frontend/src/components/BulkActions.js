import React, { useState } from 'react';

function BulkActions({ selectedFindings, allFindings, onAcknowledge, onExport, onAssign }) {
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignee, setAssignee] = useState('');
  const [exporting, setExporting] = useState(false);

  const selectedCount = selectedFindings.length;
  const isDisabled = selectedCount === 0;

  const teamMembers = [
    { id: 'team-security', name: '👤 Security Team' },
    { id: 'team-cloud', name: '☁️ Cloud Engineering' },
    { id: 'team-compliance', name: '📋 Compliance Officer' },
    { id: 'team-devops', name: '🔧 DevOps Lead' },
    { id: 'unassigned', name: '❌ Unassigned' }
  ];

  const handleAcknowledge = () => {
    if (onAcknowledge && selectedCount > 0) {
      onAcknowledge(selectedFindings);
    }
  };

  const handleExport = async () => {
    if (onExport && selectedCount > 0) {
      setExporting(true);
      try {
        await onExport(selectedFindings);
      } catch (err) {
        console.error('Export failed:', err);
      } finally {
        setExporting(false);
      }
    }
  };

  const handleAssign = () => {
    if (onAssign && selectedCount > 0 && assignee) {
      onAssign(selectedFindings, assignee);
      setAssignee('');
      setShowAssignModal(false);
    }
  };

  return (
    <div>
      {selectedCount > 0 && (
        <div style={{
          position: 'sticky',
          top: '0',
          zIndex: '100',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              fontSize: '16px',
              fontWeight: '600',
              color: '#1e293b'
            }}>
              ✓ {selectedCount} finding{selectedCount !== 1 ? 's' : ''} selected
            </div>
            <div style={{
              height: '24px',
              width: '1px',
              backgroundColor: '#e2e8f0'
            }}></div>
            <div style={{ fontSize: '13px', color: '#64748b' }}>
              Selected findings ready for bulk action
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              onClick={handleAcknowledge}
              disabled={isDisabled}
              style={{
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: '500',
                borderRadius: '6px',
                border: '1px solid #e2e8f0',
                backgroundColor: '#f1f5f9',
                color: '#1e293b',
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                opacity: isDisabled ? 0.5 : 1,
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              onMouseEnter={(e) => !isDisabled && (e.currentTarget.style.backgroundColor = '#e2e8f0')}
              onMouseLeave={(e) => !isDisabled && (e.currentTarget.style.backgroundColor = '#f1f5f9')}
            >
              ✅ Mark Acknowledged
            </button>

            <button
              onClick={() => setShowAssignModal(true)}
              disabled={isDisabled}
              style={{
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: '500',
                borderRadius: '6px',
                border: '1px solid #e2e8f0',
                backgroundColor: '#f1f5f9',
                color: '#1e293b',
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                opacity: isDisabled ? 0.5 : 1,
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              onMouseEnter={(e) => !isDisabled && (e.currentTarget.style.backgroundColor = '#e2e8f0')}
              onMouseLeave={(e) => !isDisabled && (e.currentTarget.style.backgroundColor = '#f1f5f9')}
            >
              👥 Assign To...
            </button>

            <button
              onClick={handleExport}
              disabled={isDisabled || exporting}
              style={{
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: '600',
                borderRadius: '6px',
                border: '1px solid #3b82f6',
                backgroundColor: '#3b82f6',
                color: 'white',
                cursor: isDisabled || exporting ? 'not-allowed' : 'pointer',
                opacity: isDisabled || exporting ? 0.5 : 1,
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              onMouseEnter={(e) => !isDisabled && !exporting && (e.currentTarget.style.backgroundColor = '#2563eb')}
              onMouseLeave={(e) => !isDisabled && !exporting && (e.currentTarget.style.backgroundColor = '#3b82f6')}
            >
              {exporting ? (
                <>
                  <span style={{
                    display: 'inline-block',
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    borderTop: '2px solid white',
                    borderRight: '2px solid transparent',
                    animation: 'spin 0.6s linear infinite'
                  }}></span>
                  Exporting...
                </>
              ) : (
                <>📥 Export CSV</>
              )}
            </button>
          </div>
        </div>
      )}

      {showAssignModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: '200'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '400px',
            width: '90%',
            boxShadow: '0 20px 25px rgba(0,0,0,0.15)'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
              Assign to Team Member
            </h3>

            <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#64748b' }}>
              Assigning {selectedCount} finding{selectedCount !== 1 ? 's' : ''} to:
            </p>

            <div style={{ marginBottom: '16px' }}>
              {teamMembers.map(member => (
                <label
                  key={member.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '10px 12px',
                    marginBottom: '8px',
                    borderRadius: '6px',
                    border: assignee === member.id ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                    backgroundColor: assignee === member.id ? '#f0f9ff' : 'white',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f8fafc';
                    e.currentTarget.style.borderColor = '#cbd5e1';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = assignee === member.id ? '#f0f9ff' : 'white';
                    e.currentTarget.style.borderColor = assignee === member.id ? '#3b82f6' : '#e2e8f0';
                  }}
                >
                  <input
                    type="radio"
                    name="assignee"
                    value={member.id}
                    checked={assignee === member.id}
                    onChange={(e) => setAssignee(e.target.value)}
                    style={{ marginRight: '8px', cursor: 'pointer' }}
                  />
                  <span style={{ fontSize: '14px', color: '#1e293b', fontWeight: '500' }}>
                    {member.name}
                  </span>
                </label>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setShowAssignModal(false);
                  setAssignee('');
                }}
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  fontWeight: '500',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0',
                  backgroundColor: 'white',
                  color: '#1e293b',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleAssign}
                disabled={!assignee}
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  fontWeight: '600',
                  borderRadius: '6px',
                  border: '1px solid #3b82f6',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  cursor: assignee ? 'pointer' : 'not-allowed',
                  opacity: assignee ? 1 : 0.5,
                  transition: 'all 0.2s'
                }}
              >
                Assign
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default BulkActions;
