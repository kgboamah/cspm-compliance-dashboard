/**
 * Protected Route Component
 * Location: frontend/src/components/ProtectedRoute.js
 * 
 * Wraps routes that require authentication
 * Redirects to login if not authenticated
 */
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children, requiredRole }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        <div style={{
          textAlign: 'center'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '4px solid #e2e8f0',
            borderTopColor: '#028090',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          Loading...
        </div>
      </div>
    );
  }

  // Not authenticated - redirect to login
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role if required
  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '20px'
      }}>
        <div style={{
          maxWidth: '500px',
          textAlign: 'center',
          padding: '40px',
          background: 'white',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            fontSize: '48px',
            marginBottom: '16px'
          }}>🔒</div>
          <h2 style={{
            fontSize: '24px',
            marginBottom: '12px',
            color: '#1a202c'
          }}>Access Denied</h2>
          <p style={{
            fontSize: '16px',
            color: '#718096',
            marginBottom: '24px'
          }}>
            You don't have permission to access this page.
            <br />
            Required role: <strong>{requiredRole}</strong>
            <br />
            Your role: <strong>{user?.role}</strong>
          </p>
          <button
            onClick={() => window.history.back()}
            style={{
              padding: '12px 24px',
              background: '#028090',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Authenticated and authorized - render children
  return children;
};

export default ProtectedRoute;
