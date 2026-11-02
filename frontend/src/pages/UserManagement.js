/**
 * User Management Page (Admin Only)
 * Location: frontend/src/pages/UserManagement.js
 * 
 * Allows admins to view, create, edit, and delete users
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import '../styles/UserManagement.css';

const UserManagement = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Form state
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    role: 'viewer'
  });

  // Fetch all users
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const axios = authService.createAuthAxios();
      const response = await axios.get('/api/users/');
      setUsers(response.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch users: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Handle form input changes
  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // Open create modal
  const openCreateModal = () => {
    setModalMode('create');
    setFormData({
      email: '',
      username: '',
      password: '',
      full_name: '',
      role: 'viewer'
    });
    setShowModal(true);
  };

  // Open edit modal
  const openEditModal = (user) => {
    setModalMode('edit');
    setSelectedUser(user);
    setFormData({
      email: user.email,
      username: user.username,
      password: '', // Don't show password
      full_name: user.full_name || '',
      role: user.role
    });
    setShowModal(true);
  };

  // Close modal
  const closeModal = () => {
    setShowModal(false);
    setSelectedUser(null);
    setFormData({
      email: '',
      username: '',
      password: '',
      full_name: '',
      role: 'viewer'
    });
  };

  // Create new user
  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const axios = authService.createAuthAxios();
      await axios.post('/api/users/', formData);
      await fetchUsers();
      closeModal();
      alert('User created successfully!');
    } catch (err) {
      alert('Failed to create user: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Update user
  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const axios = authService.createAuthAxios();
      const updateData = {
        full_name: formData.full_name,
        role: formData.role,
        is_active: true
      };
      await axios.put(`/api/users/${selectedUser.user_id}`, updateData);
      await fetchUsers();
      closeModal();
      alert('User updated successfully!');
    } catch (err) {
      alert('Failed to update user: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Delete user
  const handleDeleteUser = async (userId, username) => {
    if (window.confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
      try {
        const axios = authService.createAuthAxios();
        await axios.delete(`/api/users/${userId}`);
        await fetchUsers();
        alert('User deleted successfully!');
      } catch (err) {
        alert('Failed to delete user: ' + (err.response?.data?.detail || err.message));
      }
    }
  };

  // Filter users based on search
  const filteredUsers = users.filter(u =>
    u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.full_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get role badge color
  const getRoleBadgeClass = (role) => {
    switch(role.toLowerCase()) {
      case 'admin': return 'role-badge role-admin';
      case 'auditor': return 'role-badge role-auditor';
      case 'viewer': return 'role-badge role-viewer';
      default: return 'role-badge';
    }
  };

  return (
    <div className="user-management">
      <div className="page-header">
        <div>
          <h1>User Management</h1>
          <p>Manage user accounts and permissions</p>
        </div>
        <button className="btn-primary" onClick={openCreateModal}>
          <span className="icon">➕</span>
          Create User
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search users by name, username, or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading users...</p>
        </div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Full Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u) => (
                <tr key={u.user_id}>
                  <td>
                    <strong>{u.username}</strong>
                    {u.user_id === user?.user_id && (
                      <span className="you-badge">You</span>
                    )}
                  </td>
                  <td>{u.email}</td>
                  <td>{u.full_name || '-'}</td>
                  <td>
                    <span className={getRoleBadgeClass(u.role)}>
                      {u.role.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${u.is_active ? 'status-active' : 'status-inactive'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn-action btn-edit"
                        onClick={() => openEditModal(u)}
                        title="Edit user"
                      >
                        ✏️
                      </button>
                      {u.user_id !== user?.user_id && (
                        <button
                          className="btn-action btn-delete"
                          onClick={() => handleDeleteUser(u.user_id, u.username)}
                          title="Delete user"
                        >
                          🗑️
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredUsers.length === 0 && (
            <div className="no-results">
              No users found matching "{searchTerm}"
            </div>
          )}
        </div>
      )}

      {/* Modal for Create/Edit User */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{modalMode === 'create' ? 'Create New User' : 'Edit User'}</h2>
              <button className="modal-close" onClick={closeModal}>×</button>
            </div>

            <form onSubmit={modalMode === 'create' ? handleCreateUser : handleUpdateUser}>
              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  disabled={modalMode === 'edit'}
                  placeholder="user@example.com"
                />
              </div>

              <div className="form-group">
                <label htmlFor="username">Username *</label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                  disabled={modalMode === 'edit'}
                  placeholder="username"
                />
              </div>

              {modalMode === 'create' && (
                <div className="form-group">
                  <label htmlFor="password">Password *</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                    placeholder="Min 8 characters, 1 uppercase, 1 number"
                  />
                  <small>Must be at least 8 characters with 1 uppercase letter and 1 number</small>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="full_name">Full Name</label>
                <input
                  type="text"
                  id="full_name"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  placeholder="John Doe"
                />
              </div>

              <div className="form-group">
                <label htmlFor="role">Role *</label>
                <select
                  id="role"
                  name="role"
                  value={formData.role}
                  onChange={handleInputChange}
                  required
                >
                  <option value="admin">Admin - Full access</option>
                  <option value="auditor">Auditor - Read + Export</option>
                  <option value="viewer">Viewer - Read only</option>
                </select>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {modalMode === 'create' ? 'Create User' : 'Update User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
