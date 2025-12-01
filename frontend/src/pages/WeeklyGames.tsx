import React, { useEffect, useState } from 'react';
import { fetchWeeklyGames, fetchGameTouchdowns, GameData, TDScorer } from '../api/weeklyGames';

const WeeklyGames: React.FC = () => {
  const [games, setGames] = useState<GameData[]>([]);
  const [season, setSeason] = useState(2025);
  const [week, setWeek] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedGameId, setExpandedGameId] = useState<string | null>(null);
  const [touchdowns, setTouchdowns] = useState<TDScorer[]>([]);
  const [loadingTDs, setLoadingTDs] = useState(false);

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

  const handleGameClick = async (game: GameData) => {
    console.log('Game clicked:', game.game_id, 'Status:', getGameStatus(game));
    
    // If already expanded, collapse it
    if (expandedGameId === game.game_id) {
      setExpandedGameId(null);
      setTouchdowns([]);
      return;
    }

    // Only fetch TDs for completed games
    if (game.home_score === null || game.away_score === null) {
      console.log('Game not final, cannot fetch TDs');
      return;
    }

    setExpandedGameId(game.game_id);
    setLoadingTDs(true);
    try {
      console.log('Fetching touchdowns for:', game.game_id);
      const data = await fetchGameTouchdowns(game.game_id, season);
      console.log('Received touchdowns:', data.touchdowns);
      setTouchdowns(data.touchdowns);
    } catch (err) {
      console.error('Failed to fetch touchdowns:', err);
      setTouchdowns([]);
    } finally {
      setLoadingTDs(false);
    }
  };

  const getPositionColor = (position?: string) => {
    if (!position) return '#6c757d';
    switch (position) {
      case 'QB': return '#007bff';
      case 'RB': return '#28a745';
      case 'WR': return '#ffc107';
      case 'TE': return '#17a2b8';
      default: return '#dc3545';
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
            const isExpanded = expandedGameId === game.game_id;
            
            console.log(`Game ${idx}:`, {
              game_id: game.game_id,
              status,
              isFinal,
              home_score: game.home_score,
              away_score: game.away_score
            });
            
            return (
              <div 
                key={idx} 
                style={{ 
                  border: '1px solid #4a4a4a', 
                  borderRadius: '8px', 
                  padding: '1rem',
                  background: '#2a2a2a',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                  cursor: isFinal ? 'pointer' : 'default',
                  transition: 'all 0.2s ease',
                  transform: isFinal && isExpanded ? 'scale(1.01)' : 'scale(1)'
                }}
                onClick={(e) => {
                  console.log('Div clicked, isFinal:', isFinal);
                  if (isFinal) {
                    handleGameClick(game);
                  }
                }}
                onMouseEnter={(e) => {
                  if (isFinal) {
                    e.currentTarget.style.borderColor = '#b09613';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#4a4a4a';
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
                  <div style={{ fontSize: '0.85rem', color: '#b09613' }}>
                    {formatGameTime(game.gameday)}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '1rem', alignItems: 'center' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#e0e0e0' }}>
                      {game.away_team}
                    </div>
                    {isFinal && game.away_score !== null && (
                      <div style={{ 
                        fontSize: '1.5rem', 
                        fontWeight: 'bold',
                        color: game.away_score > (game.home_score || 0) ? '#13b047' : '#b09613'
                      }}>
                        {game.away_score}
                      </div>
                    )}
                  </div>

                  <div style={{ 
                    fontSize: '1.5rem', 
                    color: '#b09613',
                    padding: '0 1rem'
                  }}>
                    @
                  </div>

                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#e0e0e0' }}>
                      {game.home_team}
                    </div>
                    {isFinal && game.home_score !== null && (
                      <div style={{ 
                        fontSize: '1.5rem', 
                        fontWeight: 'bold',
                        color: game.home_score > (game.away_score || 0) ? '#13b047' : '#b09613'
                      }}>
                        {game.home_score}
                      </div>
                    )}
                  </div>
                </div>

                {!isFinal && game.gameday && (
                  <div style={{ marginTop: '0.75rem', textAlign: 'center', fontSize: '0.85rem', color: '#b09613' }}>
                    {new Date(game.gameday) > new Date() ? 'Kickoff' : 'Started'}: {formatGameTime(game.gameday)}
                  </div>
                )}

                {/* TD Scorers Section */}
                {isExpanded && (
                  <div style={{ 
                    marginTop: '1rem', 
                    paddingTop: '1rem', 
                    borderTop: '1px solid #4a4a4a'
                  }}>
                    {loadingTDs ? (
                      <div style={{ textAlign: 'center', color: '#b09613', padding: '1rem' }}>
                        Loading touchdowns...
                      </div>
                    ) : touchdowns.length > 0 ? (
                      <div>
                        <h5 style={{ marginBottom: '0.75rem', color: '#b09613', fontSize: '1rem' }}>
                          Touchdown Scorers ({touchdowns.length})
                        </h5>
                        <div style={{ display: 'grid', gap: '0.5rem' }}>
                          {touchdowns.map((td, tdIdx) => (
                            <div 
                              key={tdIdx}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                padding: '0.5rem',
                                background: '#1a1a1a',
                                borderRadius: '4px',
                                borderLeft: td.is_first_td ? '3px solid #13b047' : '3px solid #4a4a4a'
                              }}
                            >
                              <div style={{ 
                                fontWeight: 'bold', 
                                color: '#b09613',
                                minWidth: '30px'
                              }}>
                                {td.order}.
                              </div>
                              <div style={{ flex: 1 }}>
                                <div style={{ 
                                  fontWeight: 'bold', 
                                  color: '#e0e0e0',
                                  marginBottom: '0.25rem'
                                }}>
                                  {td.player}
                                  {td.is_first_td && (
                                    <span style={{ 
                                      marginLeft: '0.5rem',
                                      fontSize: '0.75rem',
                                      color: '#13b047',
                                      background: '#13b04720',
                                      padding: '0.125rem 0.375rem',
                                      borderRadius: '3px'
                                    }}>
                                      FIRST TD
                                    </span>
                                  )}
                                </div>
                                <div style={{ 
                                  fontSize: '0.85rem', 
                                  color: '#999'
                                }}>
                                  {td.team}
                                  {td.position && (
                                    <span 
                                      style={{ 
                                        marginLeft: '0.5rem',
                                        padding: '0.125rem 0.375rem',
                                        borderRadius: '3px',
                                        fontSize: '0.75rem',
                                        fontWeight: 'bold',
                                        background: getPositionColor(td.position),
                                        color: '#fff'
                                      }}
                                    >
                                      {td.position}
                                    </span>
                                  )}
                                  {td.quarter && td.time && (
                                    <span style={{ marginLeft: '0.5rem' }}>
                                      • Q{td.quarter} {td.time}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', color: '#6c757d', padding: '1rem' }}>
                        No touchdowns scored in this game
                      </div>
                    )}
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
