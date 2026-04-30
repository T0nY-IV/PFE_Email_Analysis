import React, { useEffect, useState } from 'react';
import { Mail, ChevronLeft, ChevronRight, Inbox, Database } from 'lucide-react';
import { dataAPI } from '../services/api';
import './DataPages.css';

const AllMails = () => {
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
            {data.map((item, index) => {
              const output = item.output || {};
              const type = output.workflow_type || "Unknown";
              
              let typeColor = 'gray';
              if (type === 'Réclamation') typeColor = 'red';
              if (type === 'Demande') typeColor = 'purple';
              
              return (
                <div key={index} className="email-card glass-panel">
                  <div className="card-header">
                    <div className="card-title">
                      <Mail size={16} />
                      <h4>Email #{output.email_id || index + 1}</h4>
                    </div>
                    <span className={`badge ${typeColor}`}>{type}</span>
                  </div>
                  
                  <div className="card-body">
                    <div className="info-row">
                      <span className="info-label">Sentiment:</span>
                      <span className={`badge ${output.sentiment === 'Positif' ? 'green' : output.sentiment === 'Négatif' ? 'red' : 'orange'}`}>
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
                      <p className="action-text">{output.recommended_action || "N/A"}</p>
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

export default AllMails;
