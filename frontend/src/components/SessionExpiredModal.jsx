import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import './SessionExpiredModal.css';

const SessionExpiredModal = () => {
  const { t } = useTranslation();
  const { sessionExpired, logout } = useAuth();
  const navigate = useNavigate();

  if (!sessionExpired) return null;

  const handleLoginRedirect = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="session-expired-overlay">
      <div className="session-expired-modal">
        <div className="session-expired-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 8V12M12 16H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h2>{t('session_expired_title')}</h2>
        <p>{t('session_expired_message')}</p>
        <button className="login-btn" onClick={handleLoginRedirect}>
          {t('go_to_login')}
        </button>
      </div>
    </div>
  );
};

export default SessionExpiredModal;
