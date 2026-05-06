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
  AlertCircle,
  TrendingUp,
  BarChart3,
  PieChart as PieChartIcon
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
  Legend,
  AreaChart,
  Area,
  LineChart,
  Line,
  CartesianGrid
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
      const showReclamations = user?.role === 'admin' || user?.role === 'responsable_reclamations';
      const showDemandes = user?.role === 'admin' || user?.role === 'responsable_demandes';

      const [statusRes, recTotalRes, demTotalRes, recResolvedRes, demResolvedRes] = await Promise.all([
        pollerAPI.getStatus(),
        showReclamations ? dataAPI.getReclamations(1, 1) : Promise.resolve({ data: { count: 0 } }),
        showDemandes ? dataAPI.getDemandes(1, 1) : Promise.resolve({ data: { count: 0 } }),
        showReclamations ? reclamationsAPI.getResolvedList() : Promise.resolve({ data: { count: 0 } }),
        showDemandes ? demandesAPI.getResolvedList() : Promise.resolve({ data: { count: 0 } })
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

  const showReclamations = user?.role === 'admin' || user?.role === 'responsable_reclamations';
  const showDemandes = user?.role === 'admin' || user?.role === 'responsable_demandes';

  const totalMails = (showReclamations ? stats.reclamations.total : 0) + (showDemandes ? stats.demandes.total : 0);
  const totalResolved = (showReclamations ? stats.reclamations.resolved : 0) + (showDemandes ? stats.demandes.resolved : 0);
  const totalPending = totalMails - totalResolved;

  const pieData = [];
  if (showReclamations) pieData.push({ name: 'Réclamations', value: stats.reclamations.total, color: '#ef4444' });
  if (showDemandes) pieData.push({ name: 'Demandes', value: stats.demandes.total, color: '#8b5cf6' });

  const overallStatusData = [
    { name: 'Resolved', value: totalResolved, color: '#10b981' },
    { name: 'Pending', value: totalPending, color: '#f97316' }
  ];

  const barData = [];
  if (showReclamations) {
    barData.push({
      name: 'Réclamations',
      Resolved: stats.reclamations.resolved,
      Pending: stats.reclamations.total - stats.reclamations.resolved
    });
  }
  if (showDemandes) {
    barData.push({
      name: 'Demandes',
      Resolved: stats.demandes.resolved,
      Pending: stats.demandes.total - stats.demandes.resolved
    });
  }

  // Mock trend data for area chart (in real app, fetch historical data)
  const trendData = [
    { name: 'Mon', resolved: Math.floor(totalResolved * 0.7), pending: Math.floor(totalPending * 0.8) },
    { name: 'Tue', resolved: Math.floor(totalResolved * 0.8), pending: Math.floor(totalPending * 0.9) },
    { name: 'Wed', resolved: Math.floor(totalResolved * 0.9), pending: Math.floor(totalPending * 0.95) },
    { name: 'Thu', resolved: totalResolved, pending: totalPending },
    { name: 'Fri', resolved: Math.floor(totalResolved * 1.1), pending: Math.floor(totalPending * 1.05) },
    { name: 'Sat', resolved: Math.floor(totalResolved * 1.2), pending: Math.floor(totalPending * 1.1) },
    { name: 'Sun', resolved: Math.floor(totalResolved * 1.3), pending: Math.floor(totalPending * 1.15) }
  ];

  return (
    <div className="dashboard animate-fade-in">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Welcome back, {user?.username}!</h1>
          <p>Monitor your email processing workflows in real-time</p>
          <div className="header-stats">
            <div className="mini-stat">
              <TrendingUp size={16} />
              <span>{totalMails} Total Emails</span>
            </div>
            <div className="mini-stat">
              <CheckCircle size={16} />
              <span>{((totalResolved / (totalMails || 1)) * 100).toFixed(1)}% Resolved</span>
            </div>
          </div>
        </div>
        <button
          className={`refresh-btn ${isRefreshing ? 'refreshing' : ''}`}
          onClick={fetchDashboardData}
          disabled={isRefreshing}
        >
          <Activity size={16} className={isRefreshing ? 'spin' : ''} />
          {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card glass-panel delay-100">
          <div className="stat-icon-wrapper orange">
            <Activity size={28} />
          </div>
          <div className="stat-content">
            <p className="stat-label">System Status</p>
            <h3 className="stat-value">{pollerStatus?.is_running ? 'Active' : 'Paused'}</h3>
            <div className={`stat-trend ${pollerStatus?.is_running ? 'positive' : 'negative'}`}>
              {pollerStatus?.is_running ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
              <span>{pollerStatus?.is_running ? 'Running smoothly' : 'Needs attention'}</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel delay-200">
          <div className="stat-icon-wrapper green">
            <CheckCircle size={28} />
          </div>
          <div className="stat-content">
            <p className="stat-label">Resolved Cases</p>
            <h3 className="stat-value">{totalResolved}</h3>
            <div className="stat-trend positive">
              <ArrowUpRight size={14} />
              <span>{((totalResolved / (totalMails || 1)) * 100).toFixed(1)}% success rate</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel delay-300">
          <div className="stat-icon-wrapper red">
            <AlertCircle size={28} />
          </div>
          <div className="stat-content">
            <p className="stat-label">Pending Cases</p>
            <h3 className="stat-value">{totalPending}</h3>
            <div className="stat-trend negative">
              <ArrowDownRight size={14} />
              <span>Requires action</span>
            </div>
          </div>
        </div>

        <div className="stat-card glass-panel delay-400">
          <div className="stat-icon-wrapper purple">
            <Mail size={28} />
          </div>
          <div className="stat-content">
            <p className="stat-label">Total Volume</p>
            <h3 className="stat-value">{totalMails}</h3>
            <div className="stat-trend neutral">
              <BarChart3 size={14} />
              <span>This week</span>
            </div>
          </div>
        </div>
      </div>

      <div className="analytics-section">
        <div className="chart-card glass-panel animate-slide-up">
          <div className="chart-header">
            <PieChartIcon size={20} />
            <h3>Volume Distribution</h3>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={800}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)'
                  }}
                  itemStyle={{ color: 'var(--text-primary)' }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card glass-panel animate-slide-up delay-200">
          <div className="chart-header">
            <BarChart3 size={20} />
            <h3>Resolution Performance</h3>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" />
                <XAxis
                  dataKey="name"
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <YAxis
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  contentStyle={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)'
                  }}
                />
                <Legend />
                <Bar
                  dataKey="Resolved"
                  fill="#10b981"
                  radius={[6, 6, 0, 0]}
                  animationBegin={200}
                  animationDuration={1000}
                />
                <Bar
                  dataKey="Pending"
                  fill="#f97316"
                  radius={[6, 6, 0, 0]}
                  animationBegin={400}
                  animationDuration={1000}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card glass-panel animate-slide-up delay-400">
          <div className="chart-header">
            <TrendingUp size={20} />
            <h3>Weekly Trends</h3>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="resolvedGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="pendingGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" />
                <XAxis
                  dataKey="name"
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <YAxis
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="resolved"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#resolvedGradient)"
                  strokeWidth={3}
                  animationBegin={0}
                  animationDuration={1200}
                />
                <Area
                  type="monotone"
                  dataKey="pending"
                  stroke="#f97316"
                  fillOpacity={1}
                  fill="url(#pendingGradient)"
                  strokeWidth={3}
                  animationBegin={300}
                  animationDuration={1200}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card glass-panel animate-slide-up delay-600">
          <div className="chart-header">
            <Activity size={20} />
            <h3>Resolution Rate</h3>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" />
                <XAxis
                  dataKey="name"
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <YAxis
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="resolved"
                  stroke="#8b5cf6"
                  strokeWidth={4}
                  dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 6 }}
                  activeDot={{ r: 8, stroke: '#8b5cf6', strokeWidth: 2 }}
                  animationBegin={0}
                  animationDuration={1500}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
