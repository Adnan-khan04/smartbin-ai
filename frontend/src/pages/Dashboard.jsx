import React, { useState, useEffect } from 'react';
import './Dashboard.css';

export default function Dashboard() {
  const [impact, setImpact] = useState(null);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const userStr = localStorage.getItem('user');
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      if (userStr) {
        const user = JSON.parse(userStr);
        const userId = user.user_id;

        const [impactRes, statsRes, historyRes] = await Promise.all([
          fetch(`/api/dashboard/impact/${userId}`, { headers }),
          fetch(`/api/gamification/user-stats/${userId}`, { headers }),
          fetch(`/api/dashboard/history/${userId}`, { headers }),
        ]);

        const impactData = impactRes.ok ? await impactRes.json() : null;
        const statsData = statsRes.ok ? await statsRes.json() : null;
        const historyData = historyRes.ok ? await historyRes.json() : null;

        setImpact(impactData);
        setStats(statsData);
        setHistory(historyData?.history || []);
      } else {
        // Not logged in — show global impact
        const res = await fetch('/api/dashboard/global-impact');
        const data = res.ok ? await res.json() : null;
        setImpact(data ? {
          total_items_recycled: data.total_items_recycled,
          co2_saved: data.total_co2_saved,
          plastic_recycled: data.total_plastic_recycled,
          paper_recycled: data.total_paper_recycled,
          metal_recycled: data.total_metal_recycled,
          organic_waste: 0,
        } : null);
      }
    } catch (error) {
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const WASTE_COLORS = {
    plastic: '#F59E0B',
    paper: '#3B82F6',
    metal: '#6B7280',
    organic: '#10B981',
  };

  const WASTE_EMOJIS = {
    plastic: '🧴',
    paper: '📄',
    metal: '🔩',
    organic: '🍃',
  };

  return (
    <div className="dashboard">
      <h1>Your Environmental Impact</h1>

      {loading && <div className="loading-msg">Loading your stats...</div>}

      <div className="impact-grid">
        <div className="impact-card">
          <span className="icon">♻️</span>
          <h3>Items Recycled</h3>
          <p className="value">{impact?.total_items_recycled ?? 0}</p>
        </div>
        <div className="impact-card">
          <span className="icon">💨</span>
          <h3>CO₂ Saved</h3>
          <p className="value">{(impact?.co2_saved ?? 0).toFixed(2)} kg</p>
        </div>
        <div className="impact-card">
          <span className="icon">🔴</span>
          <h3>Plastic Recycled</h3>
          <p className="value">{(impact?.plastic_recycled ?? 0).toFixed(2)} kg</p>
        </div>
        <div className="impact-card">
          <span className="icon">📄</span>
          <h3>Paper Recycled</h3>
          <p className="value">{(impact?.paper_recycled ?? 0).toFixed(2)} kg</p>
        </div>
      </div>

      <div className="stats-section">
        <h2>Your Statistics</h2>
        <div className="stats-container">
          <div className="stat">
            <label>Total Points</label>
            <p>{stats?.points ?? 0}</p>
          </div>
          <div className="stat">
            <label>Current Rank</label>
            <p>{stats?.rank ?? 'Novice'}</p>
          </div>
          <div className="stat">
            <label>Level</label>
            <p>{stats?.level ?? 1}</p>
          </div>
          <div className="stat">
            <label>Badges</label>
            <p>{stats?.badges?.length ?? 0}</p>
          </div>
        </div>
      </div>

      {history.length > 0 && (
        <div className="history-section">
          <h2>Recent Classifications</h2>
          <div className="history-list">
            {history.slice(0, 10).map((item) => (
              <div className="history-item" key={item.id}>
                <span className="history-emoji" style={{ background: WASTE_COLORS[item.waste_type] }}>
                  {WASTE_EMOJIS[item.waste_type] ?? '🗑️'}
                </span>
                <div className="history-info">
                  <span className="history-type">{item.waste_type.charAt(0).toUpperCase() + item.waste_type.slice(1)}</span>
                  <span className="history-time">{new Date(item.timestamp).toLocaleString()}</span>
                </div>
                <span className="history-points">+{item.points_earned} pts</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
