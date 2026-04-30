import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Activity, ShieldAlert, HelpCircle, ArrowUpRight, ArrowDownRight, Clock, Mail } from 'lucide-react';
import { pollerAPI } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();
  const [pollerStatus, setPollerStatus] = useState(null);
  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await pollerAPI.getStatus();
        setPollerStatus(res.data);
      } catch(err) {
        console.error(err);
      }
    };
    fetchStatus();
  }, []);

  return (
    <div className="dashboard animate-fade-in">
      <div className="dashboard-header">
        <h1>Welcome, {user?.username}</h1>
        <p>Here's what's happening with your email analysis today.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card glass-panel delay-100">
          <div className="stat-icon-wrapper orange">
            <Activity size={24} />
          </div>
          <div className="stat-content">
            <p className="stat-label">System Status</p>
            <h3 className="stat-value">
              {pollerStatus?.is_running ? 'Active' : 'Paused'}
            </h3>
            <div className={`stat-trend ${pollerStatus?.is_running ? 'positive' : 'negative'}`}>
              {pollerStatus?.is_running ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              <span>{pollerStatus?.is_running ? 'Polling' : 'Idle'}</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel delay-200">
          <div className="stat-icon-wrapper purple">
            <HelpCircle size={24} />
          </div>
          <div className="stat-content">
            <p className="stat-label">Demandes Traitées</p>
            <h3 className="stat-value">142</h3>
            <div className="stat-trend positive">
              <ArrowUpRight size={14} />
              <span>+12% this week</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel delay-300">
          <div className="stat-icon-wrapper red">
            <ShieldAlert size={24} />
          </div>
          <div className="stat-content">
            <p className="stat-label">Réclamations Ouvertes</p>
            <h3 className="stat-value">28</h3>
            <div className="stat-trend negative">
              <ArrowDownRight size={14} />
              <span>Needs attention</span>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="main-panel glass-panel">
          <div className="panel-header">
            <h3>Recent Activity</h3>
            <button className="btn-secondary">View All</button>
          </div>
          <div className="activity-list">
            <div className="activity-item">
              <div className="activity-icon blue"><Mail size={16} /></div>
              <div className="activity-details">
                <p><strong>New Email Analyzed</strong> (ID #1423)</p>
                <span className="time"><Clock size={12} /> 2 mins ago</span>
              </div>
              <span className="badge red">Réclamation</span>
            </div>
            <div className="activity-item">
              <div className="activity-icon green"><Mail size={16} /></div>
              <div className="activity-details">
                <p><strong>New Email Analyzed</strong> (ID #1422)</p>
                <span className="time"><Clock size={12} /> 15 mins ago</span>
              </div>
              <span className="badge purple">Demande</span>
            </div>
            <div className="activity-item">
              <div className="activity-icon orange"><Activity size={16} /></div>
              <div className="activity-details">
                <p><strong>Poller Started</strong> by Admin</p>
                <span className="time"><Clock size={12} /> 1 hour ago</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
