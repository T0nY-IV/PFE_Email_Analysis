import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Inbox, FileText, Database, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const Sidebar = () => {
  const { user } = useAuth();
  
  if (!user) return null;

  const role = user.role;

  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon-small"></div>
          <h2>Orange<span className="text-gradient">Analytics</span></h2>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
          <LayoutDashboard size={20} />
          <span>Dashboard</span>
        </NavLink>

        {(role === 'admin' || role === 'responsable_reclamations') && (
          <NavLink to="/reclamations" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Inbox size={20} />
            <span>Réclamations</span>
          </NavLink>
        )}

        {(role === 'admin' || role === 'responsable_demandes') && (
          <NavLink to="/demandes" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <FileText size={20} />
            <span>Demandes</span>
          </NavLink>
        )}

        {role === 'admin' && (
          <NavLink to="/all" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Database size={20} />
            <span>All Emails</span>
          </NavLink>
        )}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="avatar">{user.username.charAt(0).toUpperCase()}</div>
          <div className="user-details">
            <span className="user-name">{user.username}</span>
            <span className="user-role badge orange">{user.role.replace('_', ' ')}</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
