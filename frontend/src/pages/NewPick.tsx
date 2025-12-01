import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPick, fetchUsers, fetchGames, User, Game, CreatePickData } from '../api/picks';

const NewPick: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [games, setGames] = useState<Game[]>([]);
  const [season, setSeason] = useState(2025);
  const [week, setWeek] = useState<number>(1);
  
  const [formData, setFormData] = useState<CreatePickData>({
    user_id: 0,
    game_id: 0,
    pick_type: 'FTD',
    player_name: '',
    player_position: 'WR',
    odds: 0,
    stake: 1.0
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
    loadGames();
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
    try {
      const data = await fetchGames(season, week);
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

    if (!formData.user_id || !formData.game_id || !formData.player_name || !formData.odds) {
      setError('Please fill in all required fields');
      setLoading(false);
      return;
    }

    try {
      const result = await createPick(formData);
      setSuccess(`Pick created successfully! ${formData.pick_type}: ${formData.player_name} (${formData.odds > 0 ? '+' : ''}${formData.odds})`);
      
      if (addAnother) {
        setFormData({
          ...formData,
          player_name: '',
          odds: 0
        });
      } else {
        setTimeout(() => navigate('/week-detail'), 1500);
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
                value={week}
                onChange={(e) => setWeek(Number(e.target.value))}
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
              {games.length} games available for Week {week}
            </small>
          </div>

          {/* Pick Type */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Pick Type <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input 
                  type="radio"
                  value="FTD"
                  checked={formData.pick_type === 'FTD'}
                  onChange={(e) => setFormData({ ...formData, pick_type: e.target.value })}
                />
                First TD
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input 
                  type="radio"
                  value="ATTS"
                  checked={formData.pick_type === 'ATTS'}
                  onChange={(e) => setFormData({ ...formData, pick_type: e.target.value })}
                />
                Anytime TD
              </label>
            </div>
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

          {/* Player Position */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Position
            </label>
            <select 
              value={formData.player_position}
              onChange={(e) => setFormData({ ...formData, player_position: e.target.value })}
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            >
              <option value="WR">WR</option>
              <option value="RB">RB</option>
              <option value="TE">TE</option>
              <option value="QB">QB</option>
              <option value="UNK">Unknown</option>
            </select>
          </div>

          {/* Odds */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Odds (American) <span style={{ color: '#dc3545' }}>*</span>
            </label>
            <input 
              type="number"
              value={formData.odds || ''}
              onChange={(e) => setFormData({ ...formData, odds: Number(e.target.value) })}
              placeholder="e.g., 900 for +900 or -110"
              required
              style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
            <small style={{ color: '#6c757d', display: 'block', marginTop: '0.25rem' }}>
              Enter positive or negative number (e.g., 900 = +900, -110 = -110)
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
              onClick={() => navigate('/week-detail')}
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
