import React, { useEffect, useState } from 'react';
import { fetchWeeklyGames, GameData } from '../api/weeklyGames';

const WeeklyGames: React.FC = () => {
  const [games, setGames] = useState<GameData[]>([]);
  const [season, setSeason] = useState(2025);
  const [week, setWeek] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGames();
  }, [season, week]);

  const loadGames = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWeeklyGames(season, week);
      if (data.error) {
        setError(data.error);
        setGames([]);
      } else {
        setGames(data.games);
      }
    } catch (err: any) {
      setError(err.message);
      setGames([]);
    } finally {
      setLoading(false);
    }
  };

  const formatGameTime = (gameday: string | null) => {
    if (!gameday) return 'TBD';
    const date = new Date(gameday);
    return date.toLocaleString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getGameStatus = (game: GameData) => {
    if (game.home_score !== null && game.away_score !== null) {
      return 'FINAL';
    }
    if (!game.gameday) return 'SCHEDULED';
    const gameDate = new Date(game.gameday);
    const now = new Date();
    if (gameDate > now) return 'UPCOMING';
    return 'IN PROGRESS';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'FINAL': return '#28a745';
      case 'IN PROGRESS': return '#007bff';
      case 'UPCOMING': return '#6c757d';
      default: return '#6c757d';
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2>🏈 NFL Schedule</h2>
        <p style={{ color: '#6c757d' }}>
          Week {week} - {season} Season ({games.length} games)
        </p>
      </div>

      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <select 
          value={season} 
          onChange={(e) => setSeason(Number(e.target.value))}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
        >
          <option value={2023}>2023 Season</option>
          <option value={2024}>2024 Season</option>
          <option value={2025}>2025 Season</option>
        </select>

        <select 
          value={week} 
          onChange={(e) => setWeek(Number(e.target.value))}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
        >
          {Array.from({ length: 18 }, (_, i) => i + 1).map(w => (
            <option key={w} value={w}>Week {w}</option>
          ))}
        </select>
      </div>

      {loading && <p>Loading games...</p>}
      {error && (
        <div style={{ padding: '1rem', background: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '1rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {!loading && !error && games.length > 0 && (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {games.map((game, idx) => {
            const status = getGameStatus(game);
            const statusColor = getStatusColor(status);
            const isFinal = status === 'FINAL';
            
            return (
              <div 
                key={idx} 
                style={{ 
                  border: '1px solid #ddd', 
                  borderRadius: '8px', 
                  padding: '1rem',
                  background: 'white',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div style={{ 
                    fontSize: '0.85rem', 
                    fontWeight: 'bold', 
                    color: statusColor,
                    padding: '0.25rem 0.5rem',
                    background: `${statusColor}20`,
                    borderRadius: '4px'
                  }}>
                    {status}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#6c757d' }}>
                    {formatGameTime(game.gameday)}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '1rem', alignItems: 'center' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                      {game.away_team}
                    </div>
                    {isFinal && game.away_score !== null && (
                      <div style={{ 
                        fontSize: '1.5rem', 
                        fontWeight: 'bold',
                        color: game.away_score > (game.home_score || 0) ? '#28a745' : '#6c757d'
                      }}>
                        {game.away_score}
                      </div>
                    )}
                  </div>

                  <div style={{ 
                    fontSize: '1.5rem', 
                    color: '#6c757d',
                    padding: '0 1rem'
                  }}>
                    @
                  </div>

                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                      {game.home_team}
                    </div>
                    {isFinal && game.home_score !== null && (
                      <div style={{ 
                        fontSize: '1.5rem', 
                        fontWeight: 'bold',
                        color: game.home_score > (game.away_score || 0) ? '#28a745' : '#6c757d'
                      }}>
                        {game.home_score}
                      </div>
                    )}
                  </div>
                </div>

                {!isFinal && game.gameday && (
                  <div style={{ marginTop: '0.75rem', textAlign: 'center', fontSize: '0.85rem', color: '#6c757d' }}>
                    {new Date(game.gameday) > new Date() ? 'Kickoff' : 'Started'}: {formatGameTime(game.gameday)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {!loading && !error && games.length === 0 && (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>
          <p>No games scheduled for Week {week} of the {season} season.</p>
        </div>
      )}
    </div>
  );
};

export default WeeklyGames;
