/**
 * Authentication Service
 * Location: frontend/src/services/authService.js
 * 
 * Handles all authentication-related API calls and token management
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'cspm_auth_token';
const USER_KEY = 'cspm_user';

class AuthService {
  /**
   * Login user with email and password
   */
  async login(email, password) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        email,
        password
      });

      const { access_token, user } = response.data;

      // Store token and user in localStorage
      localStorage.setItem(TOKEN_KEY, access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));

      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Logout user
   */
  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  /**
   * Get stored token
   */
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  /**
   * Get stored user data
   */
  getUser() {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.getToken();
  }

  /**
   * Get current user info from API
   */
  async getCurrentUser() {
    try {
      const token = this.getToken();
      if (!token) {
        throw new Error('No token found');
      }

      const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      // Update stored user data
      localStorage.setItem(USER_KEY, JSON.stringify(response.data));

      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  }

  /**
   * Register new user
   */
  async register(userData) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  /**
   * Change password
   */
  async changePassword(oldPassword, newPassword) {
    try {
      const token = this.getToken();
      const response = await axios.put(
        `${API_BASE_URL}/api/auth/password`,
        {
          old_password: oldPassword,
          new_password: newPassword
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Change password error:', error);
      throw error;
    }
  }

  /**
   * Get authorization header
   */
  getAuthHeader() {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Create axios instance with auth header
   */
  createAuthAxios() {
    const instance = axios.create({
      baseURL: API_BASE_URL,
      headers: this.getAuthHeader()
    });

    // Add response interceptor to handle 401 errors
    instance.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - logout
          this.logout();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    return instance;
  }
}

export const authService = new AuthService();
export default authService;
