import React, { useEffect, useState } from 'react';
import { Mail, ChevronLeft, ChevronRight, Inbox, HelpCircle } from 'lucide-react';
import { dataAPI } from '../services/api';
import './DataPages.css';

const Demandes = () => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    fetchData();
  }, [page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await dataAPI.getDemandes(page, pageSize);
      setData(res.data.data || []);
      setTotalCount(res.data.count || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

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
            {data.map((item, index) => {
              const output = item.output || {};
              
              return (
                <div key={index} className="email-card glass-panel">
                  <div className="card-header">
                    <div className="card-title">
                      <Mail size={16} />
                      <h4>Email #{output.email_id || index + 1}</h4>
                    </div>
                    <span className="badge purple">Demande</span>
                  </div>
                  
                  <div className="card-body">
                    <div className="info-row">
                      <span className="info-label">Sentiment:</span>
                      <span className={`badge ${output.sentiment === 'Positif' ? 'green' : 'orange'}`}>
                        {output.sentiment || "Neutre"}
                      </span>
                    </div>
                    
                    <div className="info-row">
                      <span className="info-label">Keywords:</span>
                      <div className="tags">
                        {(output.keywords || []).map((kw, i) => (
                          <span key={i} className="tag">{kw}</span>
                        ))}
                      </div>
                    </div>
                    
                    <div className="info-row summary">
                      <span className="info-label">Summary:</span>
                      <p>{output.summary || "No summary provided."}</p>
                    </div>
                    
                    <div className="action-row">
                      <span className="info-label">Action:</span>
                      <p className="action-text">{output.recommended_action || "Process Request"}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {!loading && data.length > 0 && (
        <div className="pagination glass-panel">
          <button 
            className="btn-secondary" 
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft size={16} /> Prev
          </button>
          <span className="page-info">Page {page} of {totalPages}</span>
          <button 
            className="btn-secondary" 
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
};

export default Demandes;
