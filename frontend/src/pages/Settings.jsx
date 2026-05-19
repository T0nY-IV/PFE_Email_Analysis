import React, { useState } from 'react';
import { Key, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { authAPI } from '../services/api';
import './DataPages.css';

const Settings = () => {
  const { t } = useTranslation();
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleChange = (e) => {
    setPasswords({ ...passwords, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    if (passwords.new_password !== passwords.confirm_password) {
      setMessage({ type: 'error', text: t('passwords_do_not_match') });
      return;
    }

    setLoading(true);
    try {
      await authAPI.changePassword({
        current_password: passwords.current_password,
        new_password: passwords.new_password
      });
      setMessage({ type: 'success', text: t('password_changed_success') });
      setPasswords({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setMessage({ 
        type: 'error', 
        text: err.response?.data?.detail || t('failed_to_change_password')
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1>{t('user_settings')}</h1>
          <p>{t('manage_account_security')}</p>
        </div>
      </div>

      <div className="content-area" style={{ maxWidth: '600px' }}>
        <div className="glass-panel" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <Key className="text-gradient" size={24} />
            <h3 style={{ margin: 0 }}>{t('change_password_title')}</h3>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#64748b' }}>
                {t('current_password')}
              </label>
              <input
                type="password"
                name="current_password"
                value={passwords.current_password}
                onChange={handleChange}
                required
                className="input-glass"
                placeholder={t('enter_current_password')}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px' }}
              />
            </div>

            <div className="form-group">
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#64748b' }}>
                {t('new_password')}
              </label>
              <input
                type="password"
                name="new_password"
                value={passwords.new_password}
                onChange={handleChange}
                required
                className="input-glass"
                placeholder={t('enter_new_password')}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px' }}
              />
            </div>

            <div className="form-group">
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#64748b' }}>
                {t('confirm_new_password')}
              </label>
              <input
                type="password"
                name="confirm_password"
                value={passwords.confirm_password}
                onChange={handleChange}
                required
                className="input-glass"
                placeholder={t('enter_confirm_password')}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px' }}
              />
            </div>

            {message.text && (
              <div className={`status-message ${message.type}`} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem', 
                padding: '0.75rem', 
                borderRadius: '8px',
                fontSize: '0.9rem',
                backgroundColor: message.type === 'success' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                color: message.type === 'success' ? '#10b981' : '#ef4444',
                border: `1px solid ${message.type === 'success' ? '#10b981' : '#ef4444'}`
              }}>
                {message.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                {message.text}
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className="btn-primary"
              style={{ 
                marginTop: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                padding: '0.75rem'
              }}
            >
              {loading ? (
                <div className="spinner" style={{ width: '18px', height: '18px', margin: 0, borderWidth: '2px' }}></div>
              ) : (
                <>
                  <Save size={18} />
                  <span>{t('update_user')}</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Settings;
