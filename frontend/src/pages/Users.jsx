import React, { useEffect, useState } from 'react';
import { 
  Users as UsersIcon, 
  UserPlus, 
  Edit2, 
  Trash2, 
  Shield, 
  Mail, 
  Calendar, 
  MoreVertical,
  CheckCircle,
  XCircle,
  RefreshCw,
  Search,
  Filter
} from 'lucide-react';
import { authAPI } from '../services/api';
import './DataPages.css'; // Reusing some base styles
import './Users.css';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterRole, setFilterRole] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'responsable_reclamations',
    is_active: true
  });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await authAPI.getUsers(filterRole || undefined);
      setUsers(response.data);
      setError(null);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to fetch users';
      setError(errorMsg);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [filterRole]);

  const handleOpenModal = (user = null) => {
    if (user) {
      setCurrentUser(user);
      setFormData({
        username: user.username,
        email: user.email,
        password: '', // Don't show password
        role: user.role,
        is_active: user.is_active
      });
    } else {
      setCurrentUser(null);
      setFormData({
        username: '',
        email: '',
        password: '',
        role: 'responsable_reclamations',
        is_active: true
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (currentUser) {
        // Update
        const updateData = { ...formData };
        if (!updateData.password) delete updateData.password;
        await authAPI.updateUser(currentUser.id, updateData);
      } else {
        // Create
        await authAPI.createUser(formData);
      }
      setIsModalOpen(false);
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await authAPI.deleteUser(userId);
        fetchUsers();
      } catch (err) {
        alert('Failed to delete user');
      }
    }
  };

  const filteredUsers = users.filter(user => 
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'admin': return 'badge-admin';
      case 'responsable_reclamations': return 'badge-reclamation';
      case 'responsable_demandes': return 'badge-demande';
      default: return 'badge-default';
    }
  };

  const getRoleLabel = (role) => {
    switch (role) {
      case 'admin': return 'Administrator';
      case 'responsable_reclamations': return 'Complaints Manager';
      case 'responsable_demandes': return 'Requests Manager';
      default: return role;
    }
  };

  return (
    <div className="users-page animate-fade-in">
      <div className="page-header">
        <div className="header-title">
          <div className="icon-box">
            <UsersIcon size={24} />
          </div>
          <div>
            <h1>Account Management</h1>
            <p>Manage all user accounts and system permissions</p>
          </div>
        </div>
        <button className="create-btn" onClick={() => handleOpenModal()}>
          <UserPlus size={18} />
          Add New User
        </button>
      </div>

      <div className="controls-bar glass-panel">
        <div className="search-box">
          <Search size={18} />
          <input 
            type="text" 
            placeholder="Search by username or email..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filters">
          <div className="filter-item">
            <Filter size={16} />
            <select value={filterRole} onChange={(e) => setFilterRole(e.target.value)}>
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="responsable_reclamations">Complaints Manager</option>
              <option value="responsable_demandes">Requests Manager</option>
            </select>
          </div>
          <button className="refresh-btn-icon" onClick={fetchUsers} title="Refresh List">
            <RefreshCw size={18} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      <div className="users-grid">
        {error ? (
          <div className="empty-state glass-panel" style={{ color: '#ef4444' }}>
            <XCircle size={48} />
            <p>{error}</p>
          </div>
        ) : loading ? (
          <div className="loading-state">Loading users...</div>
        ) : filteredUsers.length === 0 ? (
          <div className="empty-state glass-panel">
            <UsersIcon size={48} />
            <p>No users found matching your criteria</p>
          </div>
        ) : (
          filteredUsers.map(user => (
            <div key={user.id} className="user-card glass-panel animate-slide-up">
              <div className="user-card-header">
                <div className={`user-avatar ${getRoleBadgeClass(user.role)}`}>
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div className="user-info">
                  <h3>{user.username}</h3>
                  <span className={`role-badge ${getRoleBadgeClass(user.role)}`}>
                    {getRoleLabel(user.role)}
                  </span>
                </div>
                <div className="user-status">
                  {user.is_active ? (
                    <span className="status-indicator active" title="Active Account">
                      <CheckCircle size={14} /> Active
                    </span>
                  ) : (
                    <span className="status-indicator inactive" title="Disabled Account">
                      <XCircle size={14} /> Inactive
                    </span>
                  )}
                </div>
              </div>
              
              <div className="user-card-body">
                <div className="info-row">
                  <Mail size={14} />
                  <span>{user.email}</span>
                </div>
                <div className="info-row">
                  <Calendar size={14} />
                  <span>Joined {new Date(user.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="user-card-actions">
                <button className="edit-btn" onClick={() => handleOpenModal(user)}>
                  <Edit2 size={16} />
                  Edit
                </button>
                <button 
                  className="delete-btn" 
                  onClick={() => handleDelete(user.id)}
                  disabled={user.role === 'admin' && users.filter(u => u.role === 'admin').length <= 1}
                  title={user.role === 'admin' && users.filter(u => u.role === 'admin').length <= 1 ? "Cannot delete the last admin" : ""}
                >
                  <Trash2 size={16} />
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {isModalOpen && (
        
        <div className="modal-overlay">
          <div className="modal-content glass-panel animate-scale-in">
            <div className="modal-header">
              <h2>{currentUser ? 'Edit User' : 'Create New User'}</h2>
              <button className="close-btn" onClick={() => setIsModalOpen(false)}>
                <XCircle size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label>Username</label>
                  <input 
                    type="text" 
                    required 
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Email Address</label>
                  <input 
                    type="email" 
                    required 
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>{currentUser ? 'New Password (leave blank to keep current)' : 'Password'}</label>
                  <input 
                    type="password" 
                    required={!currentUser}
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Role</label>
                  <select 
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                  >
                    <option value="admin">Admin</option>
                    <option value="responsable_reclamations">Complaints Manager</option>
                    <option value="responsable_demandes">Requests Manager</option>
                  </select>
                </div>
                <div className="form-group checkbox">
                  <label>
                    <input 
                      type="checkbox" 
                      checked={formData.is_active}
                      onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    />
                    Account Active
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="cancel-btn" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="submit-btn">{currentUser ? 'Update User' : 'Create User'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
