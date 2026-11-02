import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Settings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ text: '', type: '' });
  
  // MFA state
  const [mfaEmail, setMfaEmail] = useState('');
  const [mfaEnabling, setMfaEnabling] = useState(false);
  
  // Password change state
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [passwordChanging, setPasswordChanging] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      // Use correct token key: cspm_auth_token
      const token = localStorage.getItem('cspm_auth_token');
      const response = await axios.get('http://localhost:8000/api/auth/settings', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSettings(response.data);
      setMfaEmail(response.data.mfa_email || response.data.email);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching settings:', error);
      setMessage({ text: 'Failed to load settings', type: 'error' });
      setLoading(false);
    }
  };

  const handleMFAToggle = async () => {
    if (!settings) return;
    
    setMfaEnabling(true);
    setMessage({ text: '', type: '' });

    try {
      const token = localStorage.getItem('cspm_auth_token');
      const response = await axios.post(
        'http://localhost:8000/api/auth/mfa/toggle',
        {
          enable: !settings.mfa_enabled,
          mfa_email: !settings.mfa_enabled ? mfaEmail : null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessage({ text: response.data.message, type: 'success' });
      fetchSettings();
    } catch (error) {
      setMessage({
        text: error.response?.data?.detail || 'Failed to toggle MFA',
        type: 'error'
      });
    } finally {
      setMfaEnabling(false);
    }
  };

  const handleMFAEmailUpdate = async () => {
    setMessage({ text: '', type: '' });

    try {
      const token = localStorage.getItem('cspm_auth_token');
      const response = await axios.put(
        'http://localhost:8000/api/auth/mfa/email',
        { mfa_email: mfaEmail },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessage({ text: response.data.message, type: 'success' });
      fetchSettings();
    } catch (error) {
      setMessage({
        text: error.response?.data?.detail || 'Failed to update MFA email',
        type: 'error'
      });
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setMessage({ text: '', type: '' });

    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ text: 'New passwords do not match', type: 'error' });
      return;
    }

    if (passwordData.new_password.length < 8) {
      setMessage({ text: 'Password must be at least 8 characters', type: 'error' });
      return;
    }

    setPasswordChanging(true);

    try {
      const token = localStorage.getItem('cspm_auth_token');
      const response = await axios.put(
        'http://localhost:8000/api/auth/password',
        {
          old_password: passwordData.old_password,
          new_password: passwordData.new_password
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessage({ text: response.data.message, type: 'success' });
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      setMessage({
        text: error.response?.data?.detail || 'Failed to change password',
        type: 'error'
      });
    } finally {
      setPasswordChanging(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div>
        <div className="page-header">
          <h1>Account Settings</h1>
          <p>Unable to load settings</p>
        </div>
        {message.text && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1>Account Settings</h1>
        <p>Manage your security preferences and account information</p>
      </div>

      {message.text && (
        <div className={`alert alert-${message.type}`} style={{ marginBottom: '20px' }}>
          {message.text}
        </div>
      )}

      {/* Profile Information */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '20px', marginBottom: '16px', color: '#1e293b' }}>
          Profile Information
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', fontSize: '14px' }}>
          <div style={{ color: '#64748b' }}>Username:</div>
          <div style={{ fontWeight: '600' }}>{settings.username}</div>
          
          <div style={{ color: '#64748b' }}>Email:</div>
          <div style={{ fontWeight: '600' }}>{settings.email}</div>
          
          <div style={{ color: '#64748b' }}>Full Name:</div>
          <div style={{ fontWeight: '600' }}>{settings.full_name || 'Not set'}</div>
          
          <div style={{ color: '#64748b' }}>Role:</div>
          <div>
            <span className="badge" style={{
              backgroundColor: settings.role === 'admin' ? '#3b82f6' : 
                             settings.role === 'auditor' ? '#8b5cf6' : '#64748b',
              color: 'white', padding: '4px 12px', borderRadius: '12px', fontSize: '12px'
            }}>
              {settings.role.toUpperCase()}
            </span>
          </div>
          
          <div style={{ color: '#64748b' }}>Account Created:</div>
          <div>{new Date(settings.created_at).toLocaleDateString()}</div>
          
          <div style={{ color: '#64748b' }}>Last Login:</div>
          <div>{settings.last_login ? new Date(settings.last_login).toLocaleString() : 'Never'}</div>
        </div>
      </div>

      {/* Multi-Factor Authentication */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '20px', marginBottom: '16px', color: '#1e293b' }}>
          Multi-Factor Authentication (MFA)
        </h2>
        
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <div style={{
              fontSize: '14px',
              fontWeight: '600',
              color: settings.mfa_enabled ? '#22c55e' : '#64748b'
            }}>
              Status: {settings.mfa_enabled ? 'Enabled ✓' : 'Disabled'}
            </div>
          </div>
          
          {!settings.mfa_enabled && (
            <div style={{
              padding: '12px',
              backgroundColor: '#fef3c7',
              border: '1px solid #fbbf24',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#92400e',
              marginBottom: '16px'
            }}>
              ⚠️ Enable MFA for additional security. You'll receive a 6-digit code via email when logging in.
            </div>
          )}

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              MFA Email Address
            </label>
            <input
              type="email"
              value={mfaEmail}
              onChange={(e) => setMfaEmail(e.target.value)}
              disabled={settings.mfa_enabled}
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px 12px',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '14px'
              }}
              placeholder="email@example.com"
            />
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
              Verification codes will be sent to this email
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={handleMFAToggle}
              disabled={mfaEnabling || (!settings.mfa_enabled && !mfaEmail)}
              className="btn"
              style={{
                backgroundColor: settings.mfa_enabled ? '#ef4444' : '#3b82f6',
                color: 'white'
              }}
            >
              {mfaEnabling ? 'Processing...' : settings.mfa_enabled ? 'Disable MFA' : 'Enable MFA'}
            </button>

            {settings.mfa_enabled && (
              <button
                onClick={handleMFAEmailUpdate}
                className="btn btn-secondary"
              >
                Update MFA Email
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Change Password */}
      <div className="card">
        <h2 style={{ fontSize: '20px', marginBottom: '16px', color: '#1e293b' }}>
          Change Password
        </h2>
        
        <form onSubmit={handlePasswordChange}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              Current Password
            </label>
            <input
              type="password"
              value={passwordData.old_password}
              onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
              required
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px 12px',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              New Password
            </label>
            <input
              type="password"
              value={passwordData.new_password}
              onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
              required
              minLength="8"
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px 12px',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
              Minimum 8 characters
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: '500' }}>
              Confirm New Password
            </label>
            <input
              type="password"
              value={passwordData.confirm_password}
              onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
              required
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px 12px',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={passwordChanging}
            className="btn btn-primary"
          >
            {passwordChanging ? 'Changing Password...' : 'Change Password'}
          </button>
        </form>
      </div>

      <style>{`
        .alert {
          padding: 12px 16px;
          border-radius: 6px;
          font-size: 14px;
        }
        .alert-success {
          background-color: #dcfce7;
          color: #166534;
          border: 1px solid #86efac;
        }
        .alert-error {
          background-color: #fee2e2;
          color: #991b1b;
          border: 1px solid #fca5a5;
        }
      `}</style>
    </div>
  );
}

export default Settings;
