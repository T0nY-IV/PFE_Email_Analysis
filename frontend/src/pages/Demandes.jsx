import React, { useEffect, useState } from 'react';
import { Mail, ChevronLeft, ChevronRight, Inbox, HelpCircle, CheckCircle, X } from 'lucide-react';
import { dataAPI, demandesAPI } from '../services/api';
import EmailDetailsModal from '../components/EmailDetailsModal';
import './DataPages.css';
import { useLocation } from 'react-router-dom';

const Demandes = () => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [resolvedIds, setResolvedIds] = useState(new Set());
  const [selectedEmail, setSelectedEmail] = useState(null);
  const pageSize = 30;
  const location = useLocation();
  const searchQuery = new URLSearchParams(location.search).get('q')?.trim().toLowerCase() || '';
  const filteredData = searchQuery
    ? data.filter(item => {
        const output = item.output || {};
        const emailContent = item.input_email || '';
        const attrs = Object.values(output.attributes || {}).join(' ');
        const combined = `${output.email_id || ''} ${emailContent} ${attrs}`.toLowerCase();
        return combined.includes(searchQuery);
      })
    : data;

  useEffect(() => {
    fetchData();
  }, [page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [res, resolvedRes] = await Promise.all([
        dataAPI.getDemandes(page, pageSize),
        demandesAPI.getResolvedList().catch(() => ({ data: { resolved_uids: [] } }))
      ]);
      setData(res.data.data || []);
      setTotalCount(res.data.count || 0);
      setResolvedIds(new Set((resolvedRes.data.resolved_uids || []).map(String)));
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
      const isResolved = resolvedIds.has(idStr);
      if (isResolved) {
        await demandesAPI.markUnresolved(idStr);
        setResolvedIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(idStr);
          return newSet;
        });
      } else {
        await demandesAPI.markResolved(idStr);
        setResolvedIds(prev => {
          const newSet = new Set(prev);
          newSet.add(idStr);
          return newSet;
        });
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

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1>Demandes</h1>
          <p>Process customer requests and inquiries.</p>
        </div>
        <div className="stats-badge glass-panel">
          <HelpCircle size={18} className="text-purple-500" style={{color: '#8b5cf6'}} />
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
            {filteredData.map((item, index) => {
              const output = item.output || {};
              const emailContent = item.input_email || '';
              
              return (
                <div key={index} className="email-card glass-panel" onClick={() => setSelectedEmail(item)}>
                  <div className="card-header">
                    <div className="card-title">
                      <Mail size={16} />
                      <h4>Email #{output.email_id || index + 1}</h4>
                    </div>
                    <div className="header-actions">
                      <button 
                        className={`resolve-btn ${resolvedIds.has(String(output.email_id)) ? 'resolved' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleResolved(output.email_id);
                        }}
                        title={resolvedIds.has(String(output.email_id)) ? "Mark as Unresolved" : "Mark as Resolved"}
                      >
                        <CheckCircle size={14} />
                        <span>{resolvedIds.has(String(output.email_id)) ? 'Resolved' : 'Resolve'}</span>
                      </button>
                      <span className="badge purple">Demande</span>
                    </div>
                  </div>
                  
                  <div className="card-body">
                    <div className="info-row">
                      <span className="info-label">Attributes:</span>
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
        <div className="pagination glass-panel">
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
        </div>
      )}
    </div>
  );
};

export default Demandes;
