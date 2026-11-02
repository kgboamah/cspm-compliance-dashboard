/**
 * Main App Component - UPDATED WITH USER MANAGEMENT & SETTINGS
 * Location: frontend/src/App.js
 */
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import './App.css';

// Import pages
import Dashboard from './pages/Dashboard';
import Scans from './pages/Scans';
import Findings from './pages/Findings';
import Frameworks from './pages/Frameworks';
import Trends from './pages/Trends';
import RecurringFindings from './pages/RecurringFindings';
import UserManagement from './pages/UserManagement';
import Settings from './pages/Settings';  // <-- ADDED FOR SETTINGS
import AuditLogs from './pages/AuditLogs';

// AppLayout component with sidebar
function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">🛡️</span>
            {sidebarOpen && <span className="logo-text">CSPM Dashboard</span>}
          </div>
          <button
            className="toggle-btn"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        <nav className="sidebar-nav">
          <Link to="/" className="nav-item">
            <span className="icon">📊</span>
            {sidebarOpen && <span>Dashboard</span>}
          </Link>
          <Link to="/scans" className="nav-item">
            <span className="icon">🔍</span>
            {sidebarOpen && <span>Scans</span>}
          </Link>
          <Link to="/findings" className="nav-item">
            <span className="icon">📋</span>
            {sidebarOpen && <span>Findings</span>}
          </Link>
          <Link to="/recurring" className="nav-item">
            <span className="icon">🔁</span>
            {sidebarOpen && <span>Recurring</span>}
          </Link>
          <Link to="/frameworks" className="nav-item">
            <span className="icon">📚</span>
            {sidebarOpen && <span>Frameworks</span>}
          </Link>
          <Link to="/trends" className="nav-item">
            <span className="icon">📈</span>
            {sidebarOpen && <span>Trends</span>}
          </Link>

          {/* Divider */}
          {sidebarOpen && <div style={{ borderTop: '1px solid #e2e8f0', margin: '12px 0' }}></div>}

          {/* Settings Link - ADDED */}
          <Link to="/settings" className="nav-item">
            <span className="icon">⚙️</span>
            {sidebarOpen && <span>Settings</span>}
          </Link>

          {/* Admin-only links */}
          {user?.role === 'admin' && (
           <>
          <Link to="/audit-logs" className="nav-item">
            <span className="icon">📋</span>
            {sidebarOpen && <span>Audit Logs</span>}
          </Link>
          <Link to="/users" className="nav-item">
            <span className="icon">👥</span>
            {sidebarOpen && <span>Users</span>}
          </Link>
          </>
           )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.email?.charAt(0).toUpperCase()}
            </div>
            {sidebarOpen && (
              <div className="user-details">
                <div className="user-name">{user?.full_name || user?.username}</div>
                <div className="user-role">{user?.role?.toUpperCase()}</div>
              </div>
            )}
          </div>
          <button
            className="logout-btn"
            onClick={handleLogout}
            title="Logout"
          >
            Logout🚪
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scans" element={<Scans />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/frameworks" element={<Frameworks />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/recurring" element={<RecurringFindings />} />
          <Route path="/settings" element={<Settings />} />  {/* ADDED FOR SETTINGS */}
          <Route path="/users" element={<UserManagement />} />
          <Route path="/audit-logs" element={<AuditLogs />} />
        </Routes>
      </main>
    </div>
  );
}

// Main App component
function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
