/**
 * Login Page Component (WITH MFA SUPPORT + DEBUG LOGGING)
 * Location: frontend/src/pages/Login.js
 *
 * Beautiful login interface with email/password authentication and MFA
 */
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import MFAVerification from '../components/MFAVerification';
import '../styles/Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // MFA state
  const [showMFA, setShowMFA] = useState(false);
  const [mfaEmail, setMfaEmail] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Call backend login endpoint
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });

      const data = await response.json();

      if (response.ok) {
        // Check if MFA is required
        if (data.mfa_required) {
          console.log('🔐 MFA REQUIRED - showing verification screen');
          // Show MFA verification screen
          setMfaEmail(formData.email);
          setShowMFA(true);
          setLoading(false);
          return;
        }

        console.log('✅ Normal login (no MFA) - storing token');
        // No MFA - normal login (store token manually)
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        const from = location.state?.from?.pathname || '/';
        window.location.href = from;
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle successful MFA verification - WITH DEBUG LOGGING
  const handleMFAVerify = (data) => {
    console.log('🔐 MFA VERIFY CALLED:', data);
    console.log('📦 Access Token:', data.access_token);
    console.log('👤 User Data:', data.user);
    
    // MFA verification successful - manually set auth state
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    
    console.log('✅ Token saved to localStorage');
    console.log('📍 Current location.state:', location.state);
    
    // Navigate to dashboard with full page reload to update auth context
    const from = location.state?.from?.pathname || '/';
    console.log('🚀 Redirecting to:', from);
    
    window.location.href = from;
  };

  // Handle MFA cancel
  const handleMFACancel = () => {
    console.log('❌ MFA cancelled by user');
    setShowMFA(false);
    setFormData({ ...formData, password: '' });
  };

  // If MFA is required, show MFA verification screen
  if (showMFA) {
    console.log('📱 Rendering MFA verification screen for:', mfaEmail);
    return (
      <MFAVerification
        email={mfaEmail}
        onVerify={handleMFAVerify}
        onCancel={handleMFACancel}
      />
    );
  }

  // Normal login form
  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div className="login-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1>CSPM Dashboard</h1>
          <p>Cloud Security Posture Management</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="login-error">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                <path d="M12 8V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                <circle cx="12" cy="16" r="1" fill="currentColor"/>
              </svg>
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="admin@cspm.local"
              required
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p>Your Complete Security Posture</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
