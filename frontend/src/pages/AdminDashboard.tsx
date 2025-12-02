import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchDashboardStats, DashboardStats } from '../api/dashboard';
import { importData } from '../api/admin';
import '../styles/AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [season, setSeason] = useState<number>(2025);
  const [importLoading, setImportLoading] = useState<boolean>(false);
  const [importMessage, setImportMessage] = useState<string>('');
  const [regradeLoading, setRegradeLoading] = useState<boolean>(false);
  const [regradeMessage, setRegradeMessage] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardStats();
  }, [season]);

  const loadDashboardStats = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchDashboardStats(season);
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  const handleImportData = async () => {
    setImportLoading(true);
    setImportMessage('');
    try {
      const result = await importData(season);
      setImportMessage(result.message);
      // Reload stats after import
      await loadDashboardStats();
    } catch (err) {
      setImportMessage(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImportLoading(false);
    }
  };

  const handleGradeWeek = () => {
    if (stats) {
      navigate(`/weekly-games?week=${stats.current_week}&season=${season}`);
    }
  };

  const handleRegradeAll = async () => {
    if (!window.confirm('Re-grade ALL picks for the entire season? This will recalculate all payouts.')) {
      return;
    }

    setRegradeLoading(true);
    setRegradeMessage('');
    try {
      const response = await fetch(`http://localhost:5000/api/regrade-all?season=${season}`, {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Re-grading failed');
      }
      
      setRegradeMessage(`✅ Re-graded ${data.total_graded} picks (${data.total_won} wins, ${data.total_lost} losses)`);
      // Reload stats after re-grading
      await loadDashboardStats();
    } catch (err) {
      setRegradeMessage(err instanceof Error ? err.message : 'Re-grading failed');
    } finally {
      setRegradeLoading(false);
    }
  };

  if (loading) {
    return <div className="admin-dashboard-container"><p>Loading dashboard...</p></div>;
  }

  if (error) {
    return <div className="admin-dashboard-container"><p className="error">{error}</p></div>;
  }

  if (!stats) {
    return <div className="admin-dashboard-container"><p>No data available</p></div>;
  }

  const totalBankroll = stats.league_ftd_bankroll + stats.league_atts_bankroll;

  return (
    <div className="admin-dashboard-container">
      <div className="admin-dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="season-selector">
          <label htmlFor="season">Season: </label>
          <select
            id="season"
            value={season}
            onChange={(e) => setSeason(Number(e.target.value))}
          >
            <option value={2023}>2023</option>
            <option value={2024}>2024</option>
            <option value={2025}>2025</option>
          </select>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Active Players</div>
          <div className="stat-value">{stats.total_players}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Current Week</div>
          <div className="stat-value">Week {stats.current_week}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Picks This Week</div>
          <div className="stat-value">{stats.total_picks_this_week}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending Picks</div>
          <div className="stat-value">{stats.pending_picks}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">League Win Rate</div>
          <div className="stat-value">{stats.overall_win_rate}%</div>
        </div>
        <div className={`stat-card ${totalBankroll >= 0 ? 'positive' : 'negative'}`}>
          <div className="stat-label">Total Bankroll</div>
          <div className="stat-value">${totalBankroll.toFixed(2)}</div>
        </div>
      </div>

      {/* Bankroll Breakdown */}
      <div className="bankroll-grid">
        <div className={`bankroll-card ${stats.league_ftd_bankroll >= 0 ? 'positive' : 'negative'}`}>
          <div className="bankroll-label">FTD Bankroll</div>
          <div className="bankroll-value">${stats.league_ftd_bankroll.toFixed(2)}</div>
        </div>
        <div className={`bankroll-card ${stats.league_atts_bankroll >= 0 ? 'positive' : 'negative'}`}>
          <div className="bankroll-label">ATTS Bankroll</div>
          <div className="bankroll-value">${stats.league_atts_bankroll.toFixed(2)}</div>
        </div>
      </div>

      {/* Games Progress */}
      <div className="games-progress">
        <h3>Week {stats.current_week} Progress</h3>
        <div className="progress-info">
          <span className="progress-label">Games Graded:</span>
          <span className="progress-value">{stats.games_graded} / {stats.games_this_week}</span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${stats.games_this_week > 0 ? (stats.games_graded / stats.games_this_week * 100) : 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="actions-grid">
          <button className="action-btn primary" onClick={handleGradeWeek}>
            Grade Current Week
          </button>
          <button 
            className="action-btn secondary" 
            onClick={handleImportData}
            disabled={importLoading}
          >
            {importLoading ? 'Importing...' : 'Import NFL Data'}
          </button>
          <button className="action-btn" onClick={() => navigate('/all-picks')}>
            View All Picks
          </button>
          <button className="action-btn" onClick={() => navigate('/new-pick')}>
            Add New Pick
          </button>
          <button 
            className="action-btn warning" 
            onClick={handleRegradeAll}
            disabled={regradeLoading}
          >
            {regradeLoading ? 'Re-grading...' : 'Re-grade All Picks'}
          </button>
        </div>
        {importMessage && (
          <p className={`import-message ${importMessage.includes('failed') ? 'error' : 'success'}`}>
            {importMessage}
          </p>
        )}
        {regradeMessage && (
          <p className={`import-message ${regradeMessage.includes('failed') || regradeMessage.includes('Error') ? 'error' : 'success'}`}>
            {regradeMessage}
          </p>
        )}
      </div>

      {/* Recent Activity */}
      <div className="recent-activity">
        <h3>Recent Picks</h3>
        {stats.recent_picks.length === 0 ? (
          <p>No recent picks</p>
        ) : (
          <div className="recent-picks-table-wrapper">
            <table className="recent-picks-table">
              <thead>
                <tr>
                  <th>Week</th>
                  <th>User</th>
                  <th>Game</th>
                  <th>Type</th>
                  <th>Player</th>
                  <th>Result</th>
                  <th>Payout</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_picks.map((pick) => (
                  <tr key={pick.id}>
                    <td>{pick.week}</td>
                    <td>{pick.user_name}</td>
                    <td className="game-cell">{pick.game}</td>
                    <td>
                      <span className={`pick-type-badge ${pick.pick_type.toLowerCase()}`}>
                        {pick.pick_type}
                      </span>
                    </td>
                    <td>{pick.player_name}</td>
                    <td>
                      <span className={`result-badge ${pick.result.toLowerCase()}`}>
                        {pick.result}
                      </span>
                    </td>
                    <td className={`payout ${pick.payout > 0 ? 'positive' : pick.payout < 0 ? 'negative' : ''}`}>
                      ${pick.payout.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Navigation Grid */}
      <div className="navigation-section">
        <h3>Admin Tools</h3>
        <div className="navigation-grid">
          <div className="nav-card" onClick={() => navigate('/edit-users')}>
            <div className="nav-icon">👥</div>
            <div className="nav-title">Edit Users</div>
            <div className="nav-description">Manage league members</div>
          </div>
          <div className="nav-card" onClick={() => navigate('/grade-picks')}>
            <div className="nav-icon">⚖️</div>
            <div className="nav-title">Grade Picks</div>
            <div className="nav-description">Force grade pending picks</div>
          </div>
          <div className="nav-card" onClick={() => navigate('/import-picks')}>
            <div className="nav-icon">📥</div>
            <div className="nav-title">Import Picks</div>
            <div className="nav-description">Bulk import from CSV file</div>
          </div>
          <div className="nav-card" onClick={() => navigate('/review-picks')}>
            <div className="nav-icon">🔍</div>
            <div className="nav-title">Review Picks</div>
            <div className="nav-description">Manual review of fuzzy matches</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;

