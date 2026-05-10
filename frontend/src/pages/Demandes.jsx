import React, { useEffect, useState } from 'react';
import { Mail, ChevronLeft, ChevronRight, Inbox, HelpCircle, CheckCircle, X } from 'lucide-react';
import { dataAPI, demandesAPI } from '../services/api';
import EmailDetailsModal from '../components/EmailDetailsModal';
import './DataPages.css';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Demandes = () => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [resolvedMap, setResolvedMap] = useState({}); // Map of email_uid -> {resolved_by, resolved_at}
  const [selectedEmail, setSelectedEmail] = useState(null);
  const { user } = useAuth();
  const [pageSize, setPageSize] = useState(24);
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

  const fetchData = async () => {
    setLoading(true);
    try {
      const [res, resolvedRes] = await Promise.all([
        dataAPI.getDemandes(page, pageSize, searchQuery),
        demandesAPI.getResolvedList().catch(() => ({ data: { resolved_list: [] } }))
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
        await demandesAPI.markUnresolved(idStr);
        setResolvedMap(prev => {
          const newMap = { ...prev };
          delete newMap[idStr];
          return newMap;
        });
      } else {
        const response = await demandesAPI.markResolved(idStr);
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
          <h1>Demandes</h1>
        </div>
        <div className="stats-badge glass-panel">
          <HelpCircle size={18} className="text-purple-500" style={{ color: '#8b5cf6' }} />
          <span>{totalCount} Total Requests</span>
        </div>
      </div>

      <div className="content-area">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading records...</p>
          </div>
        ) : data.length === 0 ? (
          <div className="empty-state glass-panel">
            <Inbox size={48} className="empty-icon" />
            <h3>No Demandes Found</h3>
            <p>You're all caught up!</p>
          </div>
        ) : (
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
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleResolved(output.email_id);
                          }}
                          disabled={resolution && user?.role !== 'admin'}
                          title={resolution ? (user?.role === 'admin' ? "Mark as Unresolved" : "Only admins can unmark") : "Mark as Resolved"}
                        >
                          <CheckCircle size={14} />
                          <span>{resolution ? 'Resolved' : 'Resolve'}</span>
                        </button>
                        {resolution && (
                          <div className="resolved-info">
                            <span>By: <span className="resolver-name">{resolution.resolved_by || 'Unknown'}</span></span>
                            <span className="resolved-date">{formatResolvedAt(resolution.resolved_at)}</span>
                          </div>
                        )}
                      </div>
                      <span className="badge purple">Demande</span>
                    </div>
                  </div>

                  <div className="card-body">
                    <div className="info-row">
                      <div className="tags">24
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
                      <span className="info-label">Description:</span>
                      <p>{output.attributes?.description || "No description provided."}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal Window */}
      <EmailDetailsModal
        isOpen={!!selectedEmail}
        onClose={() => setSelectedEmail(null)}
        email={selectedEmail}
        type="Demande"
      />

      {!loading && totalCount > 0 && (
        <div className="pagination">
          <div className="pagination-info">
            <strong>{(page - 1) * pageSize + displayData.length}</strong> / <strong>{totalCount}</strong> elements
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
            <label htmlFor="pageSize">Items per page:</label>
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

export default Demandes;
