import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, Clock, ShieldAlert, CheckCircle, ChevronLeft, ChevronRight, Inbox, X } from 'lucide-react';
import { dataAPI, reclamationsAPI } from '../services/api';
import EmailDetailsModal from '../components/EmailDetailsModal';
import './DataPages.css';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Reclamations = () => {
  const { t } = useTranslation();
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [resolvedMap, setResolvedMap] = useState({}); // Map of email_uid -> {resolved_by, resolved_at}
  const [selectedEmail, setSelectedEmail] = useState(null);
  const { user } = useAuth();
  const [pageSize, setPageSize] = useState(24);
  const [viewMode, setViewMode] = useState(localStorage.getItem('viewMode') || 'cards');
  const location = useLocation();
  const searchQuery = new URLSearchParams(location.search).get('q')?.trim().toLowerCase() || '';

  // Search is now handled on the backend
  const displayData = data;

  useEffect(() => {
    // Reset to page 1 when search query changes
    setPage(1);
    fetchData();
  }, [searchQuery]);

  useEffect(() => {
    fetchData();
  }, [page, pageSize]);

  useEffect(() => {
    try { localStorage.setItem('viewMode', viewMode); } catch (e) {}
  }, [viewMode]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [res, resolvedRes] = await Promise.all([
        dataAPI.getReclamations(page, pageSize, searchQuery),
        reclamationsAPI.getResolvedList().catch(() => ({ data: { resolved_list: [] } }))
      ]);
      setData(res.data.data || []);
      setTotalCount(res.data.count || 0);

      const mapping = {};
      (resolvedRes.data.resolved_list || []).forEach(item => {
        mapping[String(item.email_uid)] = {
          resolved_by: item.resolved_by,
          resolved_at: item.resolved_at
        };
      });
      setResolvedMap(mapping);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleResolved = async (emailId) => {
    if (!emailId) return;
    const idStr = String(emailId);
    try {
      const isResolved = idStr in resolvedMap;
      if (isResolved) {
        if (user?.role !== 'admin') {
          return;
        }
        await reclamationsAPI.markUnresolved(idStr);
        setResolvedMap(prev => {
          const newMap = { ...prev };
          delete newMap[idStr];
          return newMap;
        });
      } else {
        const response = await reclamationsAPI.markResolved(idStr);
        setResolvedMap(prev => ({
          ...prev,
          [idStr]: {
            resolved_by: response.data.resolved_by,
            resolved_at: response.data.resolved_at
          }
        }));
      }
    } catch (err) {
      console.error('Failed to toggle resolved status', err);
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  const getPageNumbers = () => {
    const pages = [];
    const range = 2; // Show 2 pages before and after

    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 ||
        i === totalPages ||
        (i >= page - range && i <= page + range)
      ) {
        pages.push(i);
      } else if (i === page - range - 1 || i === page + range + 1) {
        pages.push('...');
      }
    }
    return [...new Set(pages)]; // Remove duplicates
  };

  const formatResolvedAt = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1>{t('reclamations')}</h1>
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
          <div className="view-toggle">
            <button className="view-toggle-btn" onClick={() => setViewMode(viewMode === 'cards' ? 'list' : 'cards')}>
              {viewMode === 'cards' ? t('switch_to_list_view') : t('switch_to_cards_view')}
            </button>
          </div>
          <div className="stats-badge glass-panel">
          <ShieldAlert size={18} className="text-red-500" style={{ color: '#ef4444' }} />
          <span>{totalCount} {t('total_issues')}</span>
          </div>
        </div>
      </div>

      <div className="content-area">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>{t('loading_records')}</p>
          </div>
        ) : data.length === 0 ? (
          <div className="empty-state glass-panel">
            <Inbox size={48} className="empty-icon" />
            <h3>{t('no_reclamations_found')}</h3>
            <p>{t('youre_all_caught_up')}</p>
          </div>
        ) : (
          viewMode === 'cards' ? (
            <div className="email-grid">
              {displayData.map((item, index) => {
                const output = item.output || {};
                const emailId = String(output.email_id || '');
                const resolution = resolvedMap[emailId];

                return (
                  <div key={index} className="email-card glass-panel" onClick={() => setSelectedEmail(item)}>
                    <div className="card-header">
                      <div className="card-title">
                        <Mail size={16} />
                        <h4>Email #{output.email_id || index + 1}</h4>
                      </div>
                      <div className="header-actions">
                        <div className="resolution-wrapper">
                          <button
                            className={`resolve-btn ${resolution ? 'resolved' : ''}`}
                            onClick={(e) => { e.stopPropagation(); toggleResolved(output.email_id); }}
                            disabled={resolution && user?.role !== 'admin'}
                            title={resolution ? (user?.role === 'admin' ? t('mark_as_unresolved') : t('only_admins_can_unmark')) : t('mark_as_resolved')}
                          >
                            <CheckCircle size={14} />
                            <span>{resolution ? t('resolved') : t('resolve')}</span>
                          </button>
                          {resolution && (
                            <div className="resolved-info">
                              <span>{t('by_label')} <span className="resolver-name">{resolution.resolved_by || 'Unknown'}</span></span>
                              <span className="resolved-date">{formatResolvedAt(resolution.resolved_at)}</span>
                            </div>
                          )}
                        </div>
                        <span className="badge red">{t('reclamation_label')}</span>
                      </div>
                    </div>

                    <div className="card-body">
                      <div className="info-row">
                        <div className="tags">
                          {Object.entries(output.attributes || {})
                            .filter(([key, value]) => key !== 'description' && value !== null && value !== '')
                            .map(([key, value], i) => (
                              <span key={i} className="tag">
                                <strong>{key}:</strong> {String(value)}
                              </span>
                            ))}
                        </div>
                      </div>

                      <div className="info-row summary">
                        <span className="info-label">{t('description_label')}</span>
                        <p>{output.attributes?.description || t('no_description_provided')}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="email-list">
              {displayData.map((item, index) => {
                const output = item.output || {};
                const emailId = String(output.email_id || '');
                const resolution = resolvedMap[emailId];

                return (
                  <div key={index} className="email-list-item glass-panel" onClick={() => setSelectedEmail(item)}>
                    <div className="list-left">
                      <div className="list-title">
                        <Mail size={16} />
                        <div>
                          <h4>Email #{output.email_id || index + 1}</h4>
                          <p className="list-snippet">{output.attributes?.description ? String(output.attributes.description).slice(0, 200) : t('no_description_provided')}</p>
                        </div>
                      </div>
                    </div>
                    <div className="list-right header-actions">
                      <div className="resolution-wrapper">
                        <button
                          className={`resolve-btn ${resolution ? 'resolved' : ''}`}
                          onClick={(e) => { e.stopPropagation(); toggleResolved(output.email_id); }}
                          disabled={resolution && user?.role !== 'admin'}
                          title={resolution ? (user?.role === 'admin' ? t('mark_as_unresolved') : t('only_admins_can_unmark')) : t('mark_as_resolved')}
                        >
                          <CheckCircle size={14} />
                          <span>{resolution ? t('resolved') : t('resolve')}</span>
                        </button>
                        {resolution && (
                          <div className="resolved-info">
                            <span>{t('by_label')} <span className="resolver-name">{resolution.resolved_by || 'Unknown'}</span></span>
                            <span className="resolved-date">{formatResolvedAt(resolution.resolved_at)}</span>
                          </div>
                        )}
                      </div>
                      <span className="badge red">{t('reclamation_label')}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )
        )}
      </div>

      {/* Modal Window */}
      <EmailDetailsModal
        isOpen={!!selectedEmail}
        onClose={() => setSelectedEmail(null)}
        email={selectedEmail}
        type="Reclamation"
      />

      {!loading && totalCount > 0 && (
        <div className="pagination">
          <div className="pagination-info">
            <strong>{(page - 1) * pageSize + 1}...{(page - 1) * pageSize + displayData.length}</strong> / <strong>{totalCount}</strong> elements
          </div>
          <button
            className="btn-secondary pagination-arrow"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft size={16} />
          </button>

          <div className="page-numbers">
            {getPageNumbers().map((p, idx) => (
              p === '...' ? (
                <span key={`dots-${idx}`} className="pagination-dots">...</span>
              ) : (
                <button
                  key={p}
                  className={`page-num-btn ${page === p ? 'active' : ''}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              )
            ))}
          </div>

          <button
            className="btn-secondary pagination-arrow"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            <ChevronRight size={16} />
          </button>

          <div className="page-size-selector">
            <label htmlFor="pageSize">{t('items_per_page')}</label>
            <select
              id="pageSize"
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="page-size-select"
            >
              {[8, 16, 24, 32, 40].map(size => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reclamations;
