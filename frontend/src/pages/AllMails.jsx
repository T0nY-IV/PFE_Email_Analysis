import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, ChevronLeft, ChevronRight, Inbox, Database, X } from 'lucide-react';
import { dataAPI } from '../services/api';
import EmailDetailsModal from '../components/EmailDetailsModal';
import './DataPages.css';
import { useLocation } from 'react-router-dom';

const AllMails = () => {
  const { t } = useTranslation();
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedEmail, setSelectedEmail] = useState(null);
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
      const res = await dataAPI.getAll(page, pageSize, searchQuery);
      setData(res.data.data || []);
      setTotalCount(res.data.count || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1>{t('all_emails_database')}</h1>
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
          <div className="view-toggle">
            <button className="view-toggle-btn" onClick={() => setViewMode(viewMode === 'cards' ? 'list' : 'cards')}>
              {viewMode === 'cards' ? t('switch_to_list_view') : t('switch_to_cards_view')}
            </button>
          </div>
          <div className="stats-badge glass-panel">
          <Database size={18} className="text-blue-500" style={{color: '#3b82f6'}} />
          <span>{totalCount} {t('total_processed')}</span>
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
            <h3>{t('no_emails_found')}</h3>
            <p>{t('database_empty_message')}</p>
          </div>
        ) : (
          viewMode === 'cards' ? (
            <div className="email-grid">
              {displayData.map((item, index) => {
                const output = item.output || {};
                const emailContent = item.input_email || '';
                const type = output.workflow_type || "Unknown";
                
                let typeColor = 'gray';
                if (type === 'Réclamation') typeColor = 'red';
                if (type === 'Demande') typeColor = 'purple';
                
                return (
                  <div key={index} className="email-card glass-panel" onClick={() => setSelectedEmail(item)}>
                    <div className="card-header">
                      <div className="card-title">
                        <Mail size={16} />
                        <h4>Email #{output.email_id || index + 1}</h4>
                      </div>
                      <span className={`badge ${typeColor}`}>{type}</span>
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
                const emailContent = item.input_email || '';
                const type = output.workflow_type || "Unknown";
                let typeColor = 'gray';
                if (type === 'Réclamation') typeColor = 'red';
                if (type === 'Demande') typeColor = 'purple';

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
                      <span className={`badge ${typeColor}`}>{type}</span>
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
        type={selectedEmail?.output?.workflow_type || "Unknown"}
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

export default AllMails;
