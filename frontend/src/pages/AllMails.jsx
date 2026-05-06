import React, { useEffect, useState } from 'react';
import { Mail, ChevronLeft, ChevronRight, Inbox, Database, X } from 'lucide-react';
import { dataAPI } from '../services/api';
import EmailDetailsModal from '../components/EmailDetailsModal';
import './DataPages.css';
import { useLocation } from 'react-router-dom';

const AllMails = () => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
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
      const res = await dataAPI.getAll(page, pageSize);
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
          <h1>All Emails Database</h1>
          <p>Global view of all processed emails (Admin Only).</p>
        </div>
        <div className="stats-badge glass-panel">
          <Database size={18} className="text-blue-500" style={{color: '#3b82f6'}} />
          <span>{totalCount} Total Processed</span>
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
            <h3>No Emails Found</h3>
            <p>The database is currently empty.</p>
          </div>
        ) : (
          <div className="email-grid">
            {filteredData.map((item, index) => {
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
        type={selectedEmail?.output?.workflow_type || "Unknown"}
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

export default AllMails;
