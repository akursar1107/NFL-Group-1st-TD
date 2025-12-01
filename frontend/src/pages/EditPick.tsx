import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchPicks, updatePick, Pick } from '../api/picks';
import '../styles/EditPick.css';

const EditPick: React.FC = () => {
  const { pickId } = useParams<{ pickId: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  
  // Form fields
  const [playerName, setPlayerName] = useState('');
  const [playerPosition, setPlayerPosition] = useState('WR');
  const [pickType, setPickType] = useState<'FTD' | 'ATTS'>('FTD');
  const [odds, setOdds] = useState('');
  const [stake, setStake] = useState('1.0');
  
  // Original pick data for display
  const [pickData, setPickData] = useState<Pick | null>(null);

  useEffect(() => {
    if (!pickId) {
      setError('Pick ID is required');
      setLoading(false);
      return;
    }

    const loadPick = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch all picks and find the one we need
        const response = await fetchPicks();
        const pick = response.picks.find(p => p.id === parseInt(pickId));
        
        if (!pick) {
          setError('Pick not found');
          setLoading(false);
          return;
        }
        
        setPickData(pick);
        setPlayerName(pick.player_name);
        setPlayerPosition(pick.player_position || 'WR');
        setPickType(pick.pick_type as 'FTD' | 'ATTS');
        setOdds(pick.odds.toString());
        setStake(pick.stake.toString());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load pick');
      } finally {
        setLoading(false);
      }
    };

    loadPick();
  }, [pickId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!playerName.trim()) {
      setError('Player name is required');
      return;
    }
    
    const oddsNum = parseInt(odds);
    if (isNaN(oddsNum)) {
      setError('Odds must be a valid number');
      return;
    }
    
    const stakeNum = parseFloat(stake);
    if (isNaN(stakeNum) || stakeNum <= 0) {
      setError('Stake must be a positive number');
      return;
    }
    
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    
    try {
      await updatePick(parseInt(pickId!), {
        player_name: playerName.trim(),
        player_position: playerPosition,
        pick_type: pickType,
        odds: oddsNum,
        stake: stakeNum
      });
      
      setSuccess('Pick updated successfully!');
      setTimeout(() => {
        navigate('/week-detail');
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update pick');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate('/week-detail');
  };

  if (loading) {
    return (
      <div className="edit-pick-container">
        <div className="loading">Loading pick data...</div>
      </div>
    );
  }

  if (error && !pickData) {
    return (
      <div className="edit-pick-container">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/week-detail')} className="btn-back">
          ← Back to Week Detail
        </button>
      </div>
    );
  }

  return (
    <div className="edit-pick-container">
      <div className="edit-pick-header">
        <h1>Edit Pick</h1>
        <button onClick={handleCancel} className="btn-back">
          ← Cancel
        </button>
      </div>

      {pickData && (
        <div className="pick-info">
          <h3>Pick Details</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">User:</span>
              <span className="info-value">{pickData.username}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Game:</span>
              <span className="info-value">{pickData.game_matchup}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Week:</span>
              <span className="info-value">{pickData.week}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Status:</span>
              <span className={`info-value status-${pickData.result.toLowerCase()}`}>
                {pickData.result}
              </span>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="edit-pick-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="pickType">Pick Type:</label>
            <select
              id="pickType"
              value={pickType}
              onChange={(e) => setPickType(e.target.value as 'FTD' | 'ATTS')}
              disabled={pickData?.result !== 'Pending'}
            >
              <option value="FTD">First TD</option>
              <option value="ATTS">Anytime TD</option>
            </select>
            {pickData?.result !== 'Pending' && (
              <small className="field-note">Cannot change pick type for graded picks</small>
            )}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group full-width">
            <label htmlFor="playerName">Player Name: *</label>
            <input
              type="text"
              id="playerName"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="e.g., Travis Kelce"
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="playerPosition">Position:</label>
            <select
              id="playerPosition"
              value={playerPosition}
              onChange={(e) => setPlayerPosition(e.target.value)}
            >
              <option value="QB">QB</option>
              <option value="RB">RB</option>
              <option value="WR">WR</option>
              <option value="TE">TE</option>
              <option value="FB">FB</option>
              <option value="UNK">Unknown</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="odds">Odds (American): *</label>
            <input
              type="number"
              id="odds"
              value={odds}
              onChange={(e) => setOdds(e.target.value)}
              placeholder="e.g., 900 or -110"
              required
            />
            <small className="field-note">Use + for positive odds (e.g., 900 for +900)</small>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="stake">Stake (units): *</label>
            <input
              type="number"
              id="stake"
              value={stake}
              onChange={(e) => setStake(e.target.value)}
              step="0.1"
              min="0.1"
              placeholder="e.g., 1.0"
              required
            />
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="form-actions">
          <button type="button" onClick={handleCancel} className="btn-cancel">
            Cancel
          </button>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'Updating...' : 'Update Pick'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditPick;
