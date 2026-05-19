import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Inbox, FileText, Database, Settings, ChevronLeft, ChevronRight, User } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import logoImg from '../assets/logo.png';
import './Sidebar.css';

const Sidebar = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!user) return null;

  const role = user.role;

  return (
    <aside className={`sidebar glass-panel ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <img src={logoImg} alt="Logo" className="logo-image" />
          {!isCollapsed && <h2>Orange<span className="text-gradient">Analytics</span></h2>}
        </div>
        <button
          className="collapse-toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? t('expand') : t('collapse')}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
      <div className="sidebar-footer">
        <div className="user-info">
          <div className="avatar">{user.username.charAt(0).toUpperCase()}</div>
          {!isCollapsed && (
            <div className="user-details">
              <span className="user-name">{user.username}</span>
              <span className="user-role badge orange">{user.role.replace('_', ' ')}</span>
            </div>
          )}
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
          <LayoutDashboard size={20} />
          {!isCollapsed && <span>{t('dashboard')}</span>}
        </NavLink>

        {(role === 'admin' || role === 'responsable_reclamations') && (
          <NavLink to="/reclamations" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Inbox size={20} />
            {!isCollapsed && <span>{t('reclamations')}</span>}
          </NavLink>
        )}

        {(role === 'admin' || role === 'responsable_demandes') && (
          <NavLink to="/demandes" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <FileText size={20} />
            {!isCollapsed && <span>{t('demandes')}</span>}
          </NavLink>
        )}

        {role === 'admin' && (
          <>
            <NavLink to="/all" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Database size={20} />
              {!isCollapsed && <span>{t('all_emails')}</span>}
            </NavLink>
            <NavLink to="/users" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <User size={20} />
              {!isCollapsed && <span>{t('accounts')}</span>}
            </NavLink>
          </>
        )}

        {role !== 'admin' && (
          <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Settings size={20} />
            {!isCollapsed && <span>{t('settings')}</span>}
          </NavLink>
        )}
      </nav>

      
    </aside>
  );
};

export default Sidebar;
