import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchPicks, Pick } from '../api/picks';
import { gradeWeek, gradeByType } from '../api/grading';
import '../styles/GradePicks.css';

const GradePicks: React.FC = () => {
  const navigate = useNavigate();
  const [season, setSeason] = useState(2025);
  const [week, setWeek] = useState<number | null>(null);
  const [pendingPicks, setPendingPicks] = useState<Pick[]>([]);
  const [selectedPicks, setSelectedPicks] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [grading, setGrading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadPendingPicks();
  }, [season, week]);

  const loadPendingPicks = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const data = await fetchPicks(season, week || undefined);
      const pending = data.picks.filter(p => p.result === 'Pending');
      setPendingPicks(pending);
    } catch (err) {
      setMessage({ text: err instanceof Error ? err.message : 'Failed to load picks', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePick = (pickId: number) => {
    const newSelected = new Set(selectedPicks);
    if (newSelected.has(pickId)) {
      newSelected.delete(pickId);
    } else {
      newSelected.add(pickId);
    }
    setSelectedPicks(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedPicks.size === pendingPicks.length) {
      setSelectedPicks(new Set());
    } else {
      setSelectedPicks(new Set(pendingPicks.map(p => p.id)));
    }
  };

  const handleGradeSelected = async () => {
    if (selectedPicks.size === 0) {
      setMessage({ text: 'Please select at least one pick to grade', type: 'error' });
      return;
    }

    const confirmMessage = `Are you sure you want to force grade ${selectedPicks.size} pick(s)? This will grade them based on current NFL data.`;
    if (!window.confirm(confirmMessage)) return;

    setGrading(true);
    setMessage(null);

    try {
      // Get unique weeks from selected picks
      const selectedPicksData = pendingPicks.filter(p => selectedPicks.has(p.id));
      const weeks = Array.from(new Set(selectedPicksData.map(p => p.week)));

      // Grade each week
      for (const weekNum of weeks) {
        await gradeWeek(weekNum, season);
      }

      setMessage({ 
        text: `Successfully graded ${selectedPicks.size} pick(s)`, 
        type: 'success' 
      });
      setSelectedPicks(new Set());
      await loadPendingPicks();
    } catch (err) {
      setMessage({ 
        text: err instanceof Error ? err.message : 'Failed to grade picks', 
        type: 'error' 
      });
    } finally {
      setGrading(false);
    }
  };

  const handleGradeAll = async () => {
    if (pendingPicks.length === 0) {
      setMessage({ text: 'No pending picks to grade', type: 'error' });
      return;
    }

    const confirmMessage = `Are you sure you want to grade ALL ${pendingPicks.length} pending pick(s) for season ${season}? This action cannot be undone.`;
    if (!window.confirm(confirmMessage)) return;

    setGrading(true);
    setMessage(null);

    try {
      // Get all unique weeks from pending picks
      const weeks = Array.from(new Set(pendingPicks.map(p => p.week)));

      // Grade each week
      for (const weekNum of weeks) {
        await gradeWeek(weekNum, season);
      }

      setMessage({ 
        text: `Successfully graded all ${pendingPicks.length} pending pick(s)`, 
        type: 'success' 
      });
      setSelectedPicks(new Set());
      await loadPendingPicks();
    } catch (err) {
      setMessage({ 
        text: err instanceof Error ? err.message : 'Failed to grade picks', 
        type: 'error' 
      });
    } finally {
      setGrading(false);
    }
  };

  const handleGradeAllFTD = async () => {
    const ftdPicks = pendingPicks.filter(p => p.pick_type === 'FTD');
    if (ftdPicks.length === 0) {
      setMessage({ text: 'No pending FTD picks to grade', type: 'error' });
      return;
    }

    const confirmMessage = `Are you sure you want to grade ALL ${ftdPicks.length} pending FTD pick(s) for season ${season}?`;
    if (!window.confirm(confirmMessage)) return;

    setGrading(true);
    setMessage(null);

    try {
      const result = await gradeByType('FTD', season);
      setMessage({ 
        text: result.message, 
        type: 'success' 
      });
      setSelectedPicks(new Set());
      await loadPendingPicks();
    } catch (err) {
      setMessage({ 
        text: err instanceof Error ? err.message : 'Failed to grade FTD picks', 
        type: 'error' 
      });
    } finally {
      setGrading(false);
    }
  };

  const handleGradeAllATTS = async () => {
    const attsPicks = pendingPicks.filter(p => p.pick_type === 'ATTS');
    if (attsPicks.length === 0) {
      setMessage({ text: 'No pending ATTS picks to grade', type: 'error' });
      return;
    }

    const confirmMessage = `Are you sure you want to grade ALL ${attsPicks.length} pending ATTS pick(s) for season ${season}?`;
    if (!window.confirm(confirmMessage)) return;

    setGrading(true);
    setMessage(null);

    try {
      const result = await gradeByType('ATTS', season);
      setMessage({ 
        text: result.message, 
        type: 'success' 
      });
      setSelectedPicks(new Set());
      await loadPendingPicks();
    } catch (err) {
      setMessage({ 
        text: err instanceof Error ? err.message : 'Failed to grade ATTS picks', 
        type: 'error' 
      });
    } finally {
      setGrading(false);
    }
  };

  const getAvailableWeeks = () => {
    const weeks = Array.from(new Set(pendingPicks.map(p => p.week))).sort((a, b) => a - b);
    return weeks;
  };

  return (
    <div className="grade-picks-container">
      <div className="grade-picks-header">
        <h1>⚖️ Grade Picks</h1>
        <button onClick={() => navigate('/admin')} className="btn-back">
          ← Back to Admin
        </button>
      </div>

      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="season">Season:</label>
          <select
            id="season"
            value={season}
            onChange={(e) => setSeason(parseInt(e.target.value))}
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="week">Week:</label>
          <select
            id="week"
            value={week || ''}
            onChange={(e) => setWeek(e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">All Weeks</option>
            {getAvailableWeeks().map(w => (
              <option key={w} value={w}>Week {w}</option>
            ))}
          </select>
        </div>

        <div className="action-buttons">
          <button
            onClick={handleGradeAll}
            disabled={grading || pendingPicks.length === 0}
            className="btn-grade-all"
          >
            {grading ? 'Grading...' : `Grade All (${pendingPicks.length})`}
          </button>
          <button
            onClick={handleGradeAllFTD}
            disabled={grading || pendingPicks.filter(p => p.pick_type === 'FTD').length === 0}
            className="btn-grade-ftd"
          >
            {grading ? 'Grading...' : `Grade All FTD (${pendingPicks.filter(p => p.pick_type === 'FTD').length})`}
          </button>
          <button
            onClick={handleGradeAllATTS}
            disabled={grading || pendingPicks.filter(p => p.pick_type === 'ATTS').length === 0}
            className="btn-grade-atts"
          >
            {grading ? 'Grading...' : `Grade All ATTS (${pendingPicks.filter(p => p.pick_type === 'ATTS').length})`}
          </button>
          <button
            onClick={handleGradeSelected}
            disabled={grading || selectedPicks.size === 0}
            className="btn-grade-selected"
          >
            {grading ? 'Grading...' : `Grade Selected (${selectedPicks.size})`}
          </button>
        </div>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="picks-summary">
        <div className="summary-card">
          <div className="summary-label">Pending Picks</div>
          <div className="summary-value">{pendingPicks.length}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Selected</div>
          <div className="summary-value">{selectedPicks.size}</div>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading pending picks...</div>
      ) : pendingPicks.length === 0 ? (
        <div className="no-picks">
          <p>🎉 No pending picks to grade!</p>
          <p>All picks for season {season}{week ? `, week ${week}` : ''} have been graded.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="picks-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selectedPicks.size === pendingPicks.length && pendingPicks.length > 0}
                    onChange={handleSelectAll}
                  />
                </th>
                <th>Week</th>
                <th>User</th>
                <th>Game</th>
                <th>Type</th>
                <th>Player</th>
                <th>Pos</th>
                <th>Odds</th>
                <th>Stake</th>
              </tr>
            </thead>
            <tbody>
              {pendingPicks.map(pick => (
                <tr 
                  key={pick.id}
                  className={selectedPicks.has(pick.id) ? 'selected' : ''}
                  onClick={() => handleTogglePick(pick.id)}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedPicks.has(pick.id)}
                      onChange={() => handleTogglePick(pick.id)}
                    />
                  </td>
                  <td>{pick.week}</td>
                  <td>{pick.username}</td>
                  <td className="game-cell">{pick.game_matchup}</td>
                  <td>
                    <span className={`pick-type-badge ${pick.pick_type.toLowerCase()}`}>
                      {pick.pick_type}
                    </span>
                  </td>
                  <td className="player-cell">{pick.player_name}</td>
                  <td>{pick.player_position}</td>
                  <td className="odds-cell">{pick.odds > 0 ? `+${pick.odds}` : pick.odds}</td>
                  <td>${pick.stake.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default GradePicks;
