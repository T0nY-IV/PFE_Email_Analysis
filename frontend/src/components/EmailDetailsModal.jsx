import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { X, Mail, CheckCircle, AlertCircle } from 'lucide-react';
import './EmailDetailsModal.css';

const EmailDetailsModal = ({ isOpen, onClose, email, type }) => {
  const { t } = useTranslation();
  // Lock scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen || !email) return null;

  const output = email.output || {};
  const attributes = output.attributes || {};
  const confidenceScore = output.confidence_score || 0;

  const modalContent = (
    <div className="email-modal-overlay" onClick={onClose}>
      <div className="email-modal-container" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose}>
          <X size={20} />
        </button>

        <div className="modal-inner">
          <header className="modal-headerg">
            <div className={`modal-icon-badge ${type === 'Réclamation' ? 'red' : 'purple'}`}>
              <Mail size={24} />
            </div>
            <div className="modal-title-group">
              <h3>{t('email_analysis')} - #{output.email_id}</h3>
              <span className={`type-tag ${type === 'Réclamation' ? 'red' : 'purple'}`}>
                {type}
              </span>
            </div>
          </header>
                <div>
                  <div className="confidence-meter">
                    <div className="meter-header">
                      <span>{t('ai_confidence_score')}</span>
                      <span className="percentage">{(confidenceScore * 100).toFixed(1)}%</span>
                    </div>
                    <div className="meter-track">
                      <div
                        className="meter-fill"
                        style={{ width: `${confidenceScore * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
          <table className="modal-table-layout">
            <tbody>
              <tr>
                <td className="modal-table-cell content-cell">
                  <section className="modal-section">
                    <div className="section-header">
                      <Mail size={16} />
                      <span className="section-title">{t('original_email_content')}</span>
                    </div>
                    <div className="content-scrollbox">
                      {email.input_email || t('no_content_available')}
                    </div>
                  </section>
                </td>

                <td className="modal-table-cell data-cell">
                  <section className="modal-section">
                    <div className="section-header">
                      <AlertCircle size={16} />
                      <span className="section-title">{t('extracted_data_points')}</span>
                    </div>
                    <div className="attributes-display-grid">
                      {Object.entries(attributes).map(([key, value], i) => (
                        <div key={i} className="attribute-card">
                          <span className="attribute-key">{key.replace(/_/g, ' ')}</span>
                          <span className="attribute-value">{String(value || 'N/A')}</span>
                        </div>
                      ))}
                    </div>
                  </section>
                </td>
              </tr>
            </tbody>
          </table>

        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default EmailDetailsModal;
