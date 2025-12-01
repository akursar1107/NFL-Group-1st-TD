import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPick, fetchUsers, fetchGames, User, Game, CreatePickData } from '../api/picks';
import { fetchCurrentWeek } from '../api/weeklyGames';

const NewPick: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [games, setGames] = useState<Game[]>([]);
  const [season, setSeason] = useState(2025);
  const [week, setWeek] = useState<number | null>(null);
  
  const [formData, setFormData] = useState({
    user_id: 0,
    game_id: 0,
    player_name: '',
    ftd_odds: 0,
    atts_odds: 0,
    stake: 1.0
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const initializeWeek = async () => {
      try {
        const data = await fetchCurrentWeek(season);
        setWeek(data.current_week);
      } catch (err) {
        console.error('Failed to fetch current week:', err);
        setWeek(13); // Default to week 13 if fetch fails
      }
    };
    initializeWeek();
  }, [season]);

  useEffect(() => {
    if (week !== null) {
      loadUsers();
      loadGames();
    }
  }, [season, week]);

  const loadUsers = async () => {
    try {
      const data = await fetchUsers();
      setUsers(data.users);
    } catch (err: any) {
      setError(`Failed to load users: ${err.message}`);
    }
  };

  const loadGames = async () => {
    if (week === null) return;
    try {
      const data = await fetchGames(season, week, true); // true = standalone only
      setGames(data.games);
    } catch (err: any) {
      setError(`Failed to load games: ${err.message}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent, addAnother: boolean = false) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (!formData.user_id || !formData.game_id || !formData.player_name) {
      setError('Please fill in all required fields');
      setLoading(false);
      return;
    }

    if (!formData.ftd_odds && !formData.atts_odds) {
      setError('Please enter at least one odds value (FTD or ATTS)');
      setLoading(false);
      return;
    }

    try {
      const picksCreated = [];
      
      // Create FTD pick if odds provided
      if (formData.ftd_odds) {
        const ftdPick: CreatePickData = {
          user_id: formData.user_id,
          game_id: formData.game_id,
          pick_type: 'FTD',
          player_name: formData.player_name,
          player_position: undefined,
          odds: formData.ftd_odds,
          stake: formData.stake
        };
        await createPick(ftdPick);
        picksCreated.push(`FTD (${formData.ftd_odds > 0 ? '+' : ''}${formData.ftd_odds})`);
      }
      
      // Create ATTS pick if odds provided
      if (formData.atts_odds) {
        const attsPick: CreatePickData = {
          user_id: formData.user_id,
          game_id: formData.game_id,
          pick_type: 'ATTS',
          player_name: formData.player_name,
          player_position: undefined,
          odds: formData.atts_odds,
          stake: formData.stake
        };
        await createPick(attsPick);
        picksCreated.push(`ATTS (${formData.atts_odds > 0 ? '+' : ''}${formData.atts_odds})`);
      }
      
      setSuccess(`Picks created successfully for ${formData.player_name}: ${picksCreated.join(' & ')}`);
      
      if (addAnother) {
        setFormData({
          ...formData,
          player_name: '',
          ftd_odds: 0,
          atts_odds: 0
        });
      } else {
        setTimeout(() => navigate('/weekly-games'), 1500);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2>🛡️ Add New Pick</h2>
        <p style={{ color: '#6c757d' }}>Create a new FTD or ATTS pick for a user</p>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '1rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {success && (
        <div style={{ padding: '1rem', background: '#d4edda', color: '#155724', borderRadius: '4px', marginBottom: '1rem' }}>
          <strong>Success!</strong> {success}
        </div>
      )}

      <form onSubmit={(e) => handleSubmit(e, false)}>
        <div style={{ marginBottom: '1.5rem', padding: '1.5rem', background: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          
          {/* Season & Week Selectors */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Season <span style={{ color: '#dc3545' }}>*</span>
              </label>
              <select 
                value={season}
                onChange={(e) => setSeason(Number(e.target.value))}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                <option value={2023}>2023</option>
                <option value={2024}>2024</option>
                <option value={2025}>2025</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Week <span style={{ color: '#dc3545' }}>*</span>
              </label>
              <select 
                value={week ?? 13}
                onChange={(e) => setWeek(Number(e.target.value))}
                disabled={week === null}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                {Array.from({ length: 18 }, (_, i) => i + 1).map(w => (
                  <option key={w} value={w}>Week {w}</option>
                ))}
              </select>
            </div>
          </div>

          {/* User Selection */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              User <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <select 
              value={formData.user_id}
              onChange={(e) => setFormData({ ...formData, user_id: Number(e.target.value) })}
              required
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            >
              <option value={0}>-- Select User --</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>{user.display_name}</option>
              ))}
            </select>
          </div>

          {/* Game Selection */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Game <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <select 
              value={formData.game_id}
              onChange={(e) => setFormData({ ...formData, game_id: Number(e.target.value) })}
              required
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            >
              <option value={0}>-- Select Game --</option>
              {games.map(game => (
                <option key={game.id} value={game.id}>
                  Week {game.week}: {game.matchup} ({game.game_date ? new Date(game.game_date).toLocaleDateString() : 'TBD'})
                </option>
              ))}
            </select>
            <small style={{ color: '#6c757d', display: 'block', marginTop: '0.25rem' }}>
              {games.length} standalone games available for Week {week ?? '...'}
            </small>
          </div>

          {/* Player Name */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Player Name <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <input 
              type="text"
              value={formData.player_name}
              onChange={(e) => setFormData({ ...formData, player_name: e.target.value })}
              placeholder="e.g., Jahmyr Gibbs"
              required
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </div>

          {/* First TD Odds */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              First TD Odds (American)
            </label>
            <input 
              type="number"
              value={formData.ftd_odds || ''}
              onChange={(e) => setFormData({ ...formData, ftd_odds: Number(e.target.value) })}
              placeholder="e.g., 900 for +900"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
            <small style={{ color: '#6c757d', display: 'block', marginTop: '0.25rem' }}>
              Leave blank to skip FTD pick
            </small>
          </div>

          {/* Anytime TD Odds */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Anytime TD Odds (American)
            </label>
            <input 
              type="number"
              value={formData.atts_odds || ''}
              onChange={(e) => setFormData({ ...formData, atts_odds: Number(e.target.value) })}
              placeholder="e.g., 330 for +330"
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
            <small style={{ color: '#6c757d', display: 'block', marginTop: '0.25rem' }}>
              Leave blank to skip ATTS pick
            </small>
          </div>

          {/* Stake */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Stake ($)
            </label>
            <input 
              type="number"
              step="0.01"
              value={formData.stake}
              onChange={(e) => setFormData({ ...formData, stake: Number(e.target.value) })}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
            <small style={{ color: '#6c757d', display: 'block', marginTop: '0.25rem' }}>
              Default is $1.00
            </small>
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid #ddd' }}>
            <button 
              type="button"
              onClick={() => navigate('/weekly-games')}
              style={{ 
                padding: '0.75rem 1.5rem', 
                background: '#6c757d', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px', 
                cursor: 'pointer' 
              }}
            >
              Cancel
            </button>
            <button 
              type="button"
              onClick={(e) => handleSubmit(e, true)}
              disabled={loading}
              style={{ 
                padding: '0.75rem 1.5rem', 
                background: '#17a2b8', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px', 
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1
              }}
            >
              Save & Add Another
            </button>
            <button 
              type="submit"
              disabled={loading}
              style={{ 
                padding: '0.75rem 1.5rem', 
                background: '#28a745', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px', 
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1
              }}
            >
              {loading ? 'Saving...' : 'Save Pick'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default NewPick;
