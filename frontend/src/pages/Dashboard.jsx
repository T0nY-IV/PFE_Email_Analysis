import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Activity,
  ShieldAlert,
  HelpCircle,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Mail,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import { dataAPI, pollerAPI, reclamationsAPI, demandesAPI } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const { user } = useAuth();
  const [pollerStatus, setPollerStatus] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [stats, setStats] = useState({
    reclamations: { total: 0, resolved: 0 },
    demandes: { total: 0, resolved: 0 },
    loading: true
  });

  useEffect(() => {
    fetchDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    setIsRefreshing(true);
    try {
      // Force fresh data by fetching
      const [statusRes, recTotalRes, demTotalRes, recResolvedRes, demResolvedRes] = await Promise.all([
        pollerAPI.getStatus(),
        dataAPI.getReclamations(1, 1),
        dataAPI.getDemandes(1, 1),
        reclamationsAPI.getResolvedList(),
        demandesAPI.getResolvedList()
      ]);

      console.log("Dashboard data refreshed:", new Date().toLocaleTimeString());

      const newRecCount = recTotalRes.data?.count || 0;
      const newDemCount = demTotalRes.data?.count || 0;
      const newRecResolved = recResolvedRes.data?.count || 0;
      const newDemResolved = demResolvedRes.data?.count || 0;

      setPollerStatus(statusRes.data);
      
      setStats(prev => {
        // GUARD: If the server returns 0 total emails but we previously had data, 
        // it's likely a temporary blip (server restart/file lock). Keep old data.
        const totalIncoming = newRecCount + newDemCount;
        const prevTotalIncoming = prev.reclamations.total + prev.demandes.total;
        
        if (totalIncoming === 0 && prevTotalIncoming > 0) {
          console.log("Sync Guard: Ignoring zero-data update to prevent flickering.");
          return prev;
        }

        return {
          reclamations: {
            total: newRecCount,
            resolved: newRecResolved
          },
          demandes: {
            total: newDemCount,
            resolved: newDemResolved
          },
          loading: false
        };
      });
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const totalMails = stats.reclamations.total + stats.demandes.total;
  const totalResolved = stats.reclamations.resolved + stats.demandes.resolved;
  const totalPending = totalMails - totalResolved;

  const pieData = [
    { name: 'Réclamations', value: stats.reclamations.total, color: '#ef4444' },
    { name: 'Demandes', value: stats.demandes.total, color: '#8b5cf6' }
  ];

  const overallStatusData = [
    { name: 'Resolved', value: totalResolved, color: '#10b981' },
    { name: 'Pending', value: totalPending, color: '#f97316' }
  ];

  const barData = [
    {
      name: 'Réclamations',
      Resolved: stats.reclamations.resolved,
      Pending: stats.reclamations.total - stats.reclamations.resolved
    },
    {
      name: 'Demandes',
      Resolved: stats.demandes.resolved,
      Pending: stats.demandes.total - stats.demandes.resolved
    }
  ];

  return (
    <div className="dashboard animate-fade-in">
      <div className="dashboard-header">
        <div>
          <h1>Welcome, {user?.username}</h1>
          <p>Real-time analytics for your email processing workflows.</p>
        </div>
        <button
          className={`refresh-btn ${isRefreshing ? 'refreshing' : ''}`}
          onClick={fetchDashboardData}
          disabled={isRefreshing}
        >
          <Activity size={16} className={isRefreshing ? 'spin' : ''} />
          {isRefreshing ? 'Refreshing...' : 'Refresh Stats'}
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card glass-panel delay-100">
          <div className="stat-icon-wrapper orange">
            <Activity size={24} />
          </div>
          <div className="stat-content">
            <p className="stat-label">System Poller</p>
            <h3 className="stat-value">{pollerStatus?.is_running ? 'Active' : 'Paused'}</h3>
            <div className={`stat-trend ${pollerStatus?.is_running ? 'positive' : 'negative'}`}>
              {pollerStatus?.is_running ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
              <span>{pollerStatus?.is_running ? 'Running' : 'Idle'}</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel delay-200">
          <div className="stat-icon-wrapper green">
            <CheckCircle size={24} />
          </div>
          <div className="stat-content">
            <p className="stat-label">Total Resolved</p>
            <h3 className="stat-value">{totalResolved}</h3>
            <div className="stat-trend positive">
              <ArrowUpRight size={14} />
              <span>{((totalResolved / (totalMails || 1)) * 100).toFixed(1)}% success rate</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel delay-300">
          <div className="stat-icon-wrapper red">
            <AlertCircle size={24} />
          </div>
          <div className="stat-content">
            <p className="stat-label">Total Pending</p>
            <h3 className="stat-value">{totalPending}</h3>
            <div className="stat-trend negative">
              <ArrowDownRight size={14} />
              <span>Action required</span>
            </div>
          </div>
        </div>
      </div>

      <div className="analytics-section">
        <div className="chart-card glass-panel">
          <h3>Total Volume Distribution</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#131b2f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card glass-panel">
          <h3>Overall Resolution Status</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={overallStatusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {overallStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#131b2f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card glass-panel">
          <h3>Resolution Performance</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={barData}>
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  contentStyle={{ background: '#131b2f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                />
                <Legend />
                <Bar dataKey="Resolved" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Pending" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>

  );
};

export default Dashboard;
