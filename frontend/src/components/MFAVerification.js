/**
 * MFA Verification Component (CORRECT KEYS FOR AUTHSERVICE)
 * Location: frontend/src/components/MFAVerification.js
 */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/MFAVerification.css';

const MFAVerification = ({ email, onCancel }) => {
  const navigate = useNavigate();
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const inputRefs = useRef([]);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleChange = (index, value) => {
    if (value && !/^\d$/.test(value)) return;
    
    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    setError('');

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (value && index === 5 && newCode.every(digit => digit)) {
      console.log('🔢 All 6 digits entered, auto-submitting...');
      handleVerify(newCode.join(''));
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    
    if (/^\d+$/.test(pastedData)) {
      const newCode = pastedData.split('').concat(Array(6).fill('')).slice(0, 6);
      setCode(newCode);
      
      const focusIndex = Math.min(pastedData.length, 5);
      inputRefs.current[focusIndex]?.focus();

      if (pastedData.length === 6) {
        console.log('📋 Full 6-digit code pasted, auto-submitting...');
        handleVerify(pastedData);
      }
    }
  };

  const handleVerify = async (codeString) => {
    const verificationCode = codeString || code.join('');
    
    if (verificationCode.length !== 6) {
      setError('Please enter all 6 digits');
      return;
    }

    setLoading(true);
    setError('');

    try {
      console.log('🔐 Verifying MFA code...');
      const response = await fetch('http://localhost:8000/api/auth/mfa/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          code: verificationCode
        })
      });

      const data = await response.json();
      console.log('📥 MFA API Response:', response.status);

      if (response.ok) {
        console.log('✅ MFA VERIFICATION SUCCESSFUL!');
        console.log('💾 Saving token with authService keys: cspm_auth_token & cspm_user');
        
        // CORRECT: Use the same keys as authService
        localStorage.setItem('cspm_auth_token', data.access_token);
        localStorage.setItem('cspm_user', JSON.stringify(data.user));
        
        console.log('✅ Token saved successfully');
        console.log('🚀 Redirecting to dashboard...');
        
        // Redirect to dashboard with full page reload
        window.location.href = '/';
      } else {
        console.log('❌ MFA verification failed:', data);
        setError(data.detail || 'Invalid verification code');
        setCode(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (err) {
      console.error('💥 MFA verification error:', err);
      setError('Verification failed. Please try again.');
      setCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    console.log('🔄 Resending MFA code...');
    setResending(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/auth/mfa/resend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      if (response.ok) {
        console.log('✅ Code resent successfully');
        setCountdown(60);
        alert('New code sent to your email!');
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to resend code');
      }
    } catch (err) {
      console.error('💥 Resend error:', err);
      setError('Failed to resend code. Please try again.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="mfa-container">
      <div className="mfa-card">
        <div className="mfa-icon">🔐</div>
        <h2>Two-Factor Authentication</h2>
        <p className="mfa-description">
          Enter the 6-digit code sent to your email
        </p>
        <p className="mfa-email">{email}</p>

        <div className="mfa-code-inputs">
          {code.map((digit, index) => (
            <input
              key={index}
              ref={el => inputRefs.current[index] = el}
              type="text"
              inputMode="numeric"
              maxLength="1"
              value={digit}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              onPaste={index === 0 ? handlePaste : undefined}
              className="mfa-code-input"
              autoFocus={index === 0}
              disabled={loading}
            />
          ))}
        </div>

        {error && (
          <div className="mfa-error">
            ⚠️ {error}
          </div>
        )}

        <div className="mfa-actions">
          <button
            className="btn-verify"
            onClick={() => handleVerify()}
            disabled={loading || code.some(d => !d)}
          >
            {loading ? 'Verifying...' : 'Verify Code'}
          </button>
          <button
            className="btn-resend"
            onClick={handleResend}
            disabled={resending || countdown > 0}
          >
            {resending ? 'Sending...' : countdown > 0 ? `Resend (${countdown}s)` : 'Resend Code'}
          </button>
          <button
            className="btn-cancel"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
        </div>

        <div className="mfa-help">
          <p>💡 Didn't receive the code?</p>
          <ul>
            <li>Check your spam/junk folder</li>
            <li>Wait up to 1 minute for delivery</li>
            <li>Click "Resend Code" to request a new one</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MFAVerification;
