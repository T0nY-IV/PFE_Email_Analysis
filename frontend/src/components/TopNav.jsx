import React, { useEffect, useState } from 'react';
import { LogOut, Bell, Search, Activity, Play, Square, RefreshCw, Timer } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { pollerAPI } from '../services/api';
import './TopNav.css';

const TopNav = () => {
  const { logout } = useAuth();
  const [pollerStatus, setPollerStatus] = useState({ is_running: false });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [cooldownTime, setCooldownTime] = useState(60);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await pollerAPI.getStatus();
      setPollerStatus(res.data);
    } catch (err) {
      console.error("Failed to fetch poller status", err);
    }
  };

  const handleStart = async () => {
    try {
      await pollerAPI.start(cooldownTime);
      fetchStatus();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStop = async () => {
    try {
      await pollerAPI.stop();
      fetchStatus();
    } catch (err) {
      console.error(err);
    }
  };

  const handleFetchOnce = async () => {
    setIsRefreshing(true);
    try {
      await pollerAPI.fetchOnce();
    } catch (err) {
      console.error(err);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <header className="topnav glass-panel">
      <div className="search-bar">
        <Search size={18} className="search-icon" />
        <input type="text" placeholder="Search emails, subjects..." className="search-input" />
      </div>

      <div className="topnav-actions">
        <div className="poller-controls">
          <div className="status-indicator">
            <span className={`status-dot ${pollerStatus.is_running ? 'running' : 'stopped'}`}></span>
            <span className="status-text">{pollerStatus.is_running ? 'Poller Active' : 'Poller Paused'}</span>
          </div>
          <div className="cooldown-wrapper">
            <Timer size={14} className="cooldown-icon" />
            <input 
              type="number" 
              className="cooldown-input" 
              value={cooldownTime}
              onChange={(e) => setCooldownTime(Number(e.target.value))}
              min="10"
              title="Cooldown time in seconds"
            />
            <span className="cooldown-unit">s</span>
          </div>
          
          <div className="action-buttons">
            {!pollerStatus.is_running ? (
              <button className="icon-btn start" onClick={handleStart} title="Start Poller">
                <Play size={16} />
              </button>
            ) : (
              <>
                <button className="icon-btn stop" onClick={handleStop} title="Stop Poller">
                  <Square size={16} />
                </button>
                <button className="icon-btn start" onClick={handleStart} title="Restart with new cooldown">
                  <Play size={16} />
                </button>
              </>
            )}
            <button 
              className={`icon-btn refresh ${isRefreshing ? 'spin' : ''}`} 
              onClick={handleFetchOnce}
              title="Fetch Once"
            >
              <RefreshCw size={16} />
            </button>
          </div>
        </div>

        <div className="divider"></div>

        <button className="icon-btn">
          <Bell size={20} />
          <span className="notification-dot"></span>
        </button>
        
        <button className="icon-btn logout-btn" onClick={logout} title="Logout">
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
};

export default TopNav;
