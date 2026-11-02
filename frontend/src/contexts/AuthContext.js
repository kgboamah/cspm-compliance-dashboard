/**
 * Authentication Context
 * Location: frontend/src/contexts/AuthContext.js
 * 
 * Provides global authentication state and methods
 */
import React, { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    const initAuth = async () => {
      const savedToken = authService.getToken();
      
      if (savedToken) {
        try {
          // Verify token is still valid by fetching user info
          const userData = await authService.getCurrentUser();
          setUser(userData);
          setToken(savedToken);
        } catch (error) {
          console.error('Token validation failed:', error);
          authService.logout();
        }
      }
      
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authService.login(email, password);
      setUser(response.user);
      setToken(response.access_token);
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed. Please try again.' 
      };
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const hasRole = (role) => {
    return user?.role === role;
  };

  const isAdmin = () => {
    return user?.role === 'admin';
  };

  const isAuditor = () => {
    return user?.role === 'auditor';
  };

  const isViewer = () => {
    return user?.role === 'viewer';
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated,
    hasRole,
    isAdmin,
    isAuditor,
    isViewer
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
