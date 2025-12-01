import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchWeekDetail, GameDetailData } from '../api/weekDetail';
import { deletePick } from '../api/picks';

const WeekDetail: React.FC = () => {
  const navigate = useNavigate();
  const [games, setGames] = useState<GameDetailData[]>([]);
  const [season, setSeason] = useState(2025);
  const [week, setWeek] = useState<number>(1);
  const [availableWeeks, setAvailableWeeks] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [grading, setGrading] = useState(false);
  const [gradingResult, setGradingResult] = useState<string | null>(null);
  const [showGradeConfirm, setShowGradeConfirm] = useState(false);

  useEffect(() => {
    loadWeekDetail();
  }, [season, week]);

  const loadWeekDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWeekDetail(season, week);
      if (data.error) {
        setError(data.error);
        setGames([]);
      } else {
        setGames(data.games);
        setAvailableWeeks(data.available_weeks);
      }
    } catch (err: any) {
      setError(err.message);
      setGames([]);
    } finally {
      setLoading(false);
    }
  };

  const getResultBadge = (result: string) => {
    const styles: Record<string, { bg: string; color: string }> = {
      'W': { bg: '#d4edda', color: '#155724' },
      'L': { bg: '#f8d7da', color: '#721c24' },
      'Pending': { bg: '#fff3cd', color: '#856404' },
      'Push': { bg: '#d1ecf1', color: '#0c5460' }
    };
    const style = styles[result] || styles['Pending'];
    return (
      <span style={{
        padding: '0.25rem 0.5rem',
        background: style.bg,
        color: style.color,
        borderRadius: '4px',
        fontSize: '0.85rem',
        fontWeight: 'bold'
      }}>
        {result}
      </span>
    );
  };

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  const formatPayout = (payout: number) => {
    const sign = payout >= 0 ? '+' : '';
    return `${sign}$${payout.toFixed(2)}`;
  };

  const handleDeletePick = async (pickId: number) => {
    try {
      await deletePick(pickId);
      setDeleteConfirm(null);
      loadWeekDetail(); // Reload data
    } catch (err: any) {
      setError(`Failed to delete pick: ${err.message}`);
    }
  };

  const handleGradeWeek = async () => {
    setGrading(true);
    setError(null);
    setGradingResult(null);
    
    try {
      const response = await fetch('http://localhost:5000/api/grade-week', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ week, season }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to grade week');
      }
      
      setGradingResult(
        `✅ Week ${week} graded! ${data.total_graded} picks: ${data.total_won} wins, ${data.total_lost} losses` +
        (data.total_needs_review > 0 ? `, ${data.total_needs_review} need review` : '')
      );
      setShowGradeConfirm(false);
      
      // Reload the week data to show updated results
      setTimeout(() => loadWeekDetail(), 1000);
    } catch (err: any) {
      setError(`Grading failed: ${err.message}`);
      setShowGradeConfirm(false);
    } finally {
      setGrading(false);
    }
  };

  const formatGameTime = (gameDate: string | null, gameTime: string | null) => {
    if (!gameDate) return 'TBD';
    const date = new Date(gameDate);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2>🏈 Week {week} Games & Picks</h2>
        <p style={{ color: '#6c757d' }}>
          {season} Season - All picks and results
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
          {availableWeeks && availableWeeks.length > 0 ? (
            availableWeeks.map(w => (
              <option key={w} value={w}>Week {w}</option>
            ))
          ) : (
            Array.from({ length: 18 }, (_, i) => i + 1).map(w => (
              <option key={w} value={w}>Week {w}</option>
            ))
          )}
        </select>

        <button 
          onClick={loadWeekDetail}
          style={{ 
            padding: '0.5rem 1rem', 
            background: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: 'pointer' 
          }}
        >
          🔄 Refresh
        </button>

        <button 
          onClick={() => setShowGradeConfirm(true)}
          disabled={grading || games.length === 0}
          style={{ 
            padding: '0.5rem 1rem', 
            background: '#28a745', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: (grading || games.length === 0) ? 'not-allowed' : 'pointer',
            opacity: (grading || games.length === 0) ? 0.6 : 1,
            marginLeft: 'auto'
          }}
        >
          {grading ? '⏳ Grading...' : '✓ Grade Week'}
        </button>
      </div>

      {showGradeConfirm && (
        <div style={{ 
          marginBottom: '1rem', 
          padding: '1rem', 
          background: '#fff3cd', 
          border: '1px solid #ffc107', 
          borderRadius: '4px' 
        }}>
          <p style={{ margin: '0 0 0.75rem 0', fontWeight: 'bold' }}>
            ⚠️ Confirm Grading
          </p>
          <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem' }}>
            This will automatically grade all picks for Week {week} based on actual game results. 
            Picks will be marked as Win (W) or Loss (L) and payouts will be calculated.
          </p>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleGradeWeek}
              disabled={grading}
              style={{
                padding: '0.5rem 1rem',
                background: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: grading ? 'not-allowed' : 'pointer',
                opacity: grading ? 0.6 : 1
              }}
            >
              Confirm Grade
            </button>
            <button
              onClick={() => setShowGradeConfirm(false)}
              disabled={grading}
              style={{
                padding: '0.5rem 1rem',
                background: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: grading ? 'not-allowed' : 'pointer',
                opacity: grading ? 0.6 : 1
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {gradingResult && (
        <div style={{ 
          padding: '1rem', 
          background: '#d4edda', 
          color: '#155724', 
          borderRadius: '4px', 
          marginBottom: '1rem' 
        }}>
          {gradingResult}
        </div>
      )}

      {loading && <p>Loading week data...</p>}
      {error && (
        <div style={{ padding: '1rem', background: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '1rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {!loading && !error && games.length > 0 && (
        <div style={{ display: 'grid', gap: '2rem' }}>
          {games.map((game, idx) => {
            const allPicks = [...game.ftd_picks, ...game.atts_picks];
            const pendingCount = allPicks.filter(p => p.result === 'Pending').length;
            const winCount = allPicks.filter(p => p.result === 'W').length;
            const lossCount = allPicks.filter(p => p.result === 'L').length;

            return (
              <div 
                key={idx}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  background: 'white',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
              >
                {/* Game Header */}
                <div style={{ marginBottom: '1rem', borderBottom: '2px solid #007bff', paddingBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.5rem' }}>{game.matchup}</h3>
                      <div style={{ color: '#6c757d', fontSize: '0.9rem', marginTop: '0.25rem' }}>
                        {formatGameTime(game.game_date, game.game_time)}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      {game.is_final ? (
                        <div>
                          <div style={{ fontSize: '0.85rem', color: '#28a745', fontWeight: 'bold' }}>FINAL</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                            {game.away_score} - {game.home_score}
                          </div>
                        </div>
                      ) : (
                        <div style={{ fontSize: '0.85rem', color: '#6c757d' }}>Scheduled</div>
                      )}
                    </div>
                  </div>
                  {game.actual_first_td_player && (
                    <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: '#d4edda', borderRadius: '4px' }}>
                      <strong>First TD:</strong> {game.actual_first_td_player}
                    </div>
                  )}
                </div>

                {/* Pick Summary */}
                <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', fontSize: '0.9rem' }}>
                  <div>📊 <strong>{game.total_picks}</strong> picks</div>
                  <div>✅ <strong>{winCount}</strong> wins</div>
                  <div>❌ <strong>{lossCount}</strong> losses</div>
                  <div>⏳ <strong>{pendingCount}</strong> pending</div>
                </div>

                {/* FTD Picks */}
                {game.ftd_picks.length > 0 && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <h4 style={{ margin: '0 0 0.75rem 0', color: '#007bff' }}>🎯 First TD Picks</h4>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                        <thead>
                          <tr style={{ borderBottom: '2px solid #ddd', background: '#f8f9fa' }}>
                            <th style={{ padding: '0.5rem', textAlign: 'left' }}>User</th>
                            <th style={{ padding: '0.5rem', textAlign: 'left' }}>Player</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Pos</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Odds</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Stake</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Result</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Payout</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {game.ftd_picks.map(pick => (
                            <tr key={pick.id} style={{ borderBottom: '1px solid #ddd' }}>
                              <td style={{ padding: '0.5rem' }}>{pick.username}</td>
                              <td style={{ padding: '0.5rem', fontWeight: 'bold' }}>{pick.player_name}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{pick.player_position}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{formatOdds(pick.odds)}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>${pick.stake.toFixed(2)}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{getResultBadge(pick.result)}</td>
                              <td style={{ 
                                padding: '0.5rem', 
                                textAlign: 'center',
                                color: pick.payout >= 0 ? '#28a745' : '#dc3545',
                                fontWeight: 'bold'
                              }}>
                                {formatPayout(pick.payout)}
                              </td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                {deleteConfirm === pick.id ? (
                                  <div style={{ display: 'flex', gap: '0.25rem', justifyContent: 'center' }}>
                                    <button
                                      onClick={() => handleDeletePick(pick.id)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#dc3545',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      Confirm
                                    </button>
                                    <button
                                      onClick={() => setDeleteConfirm(null)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#6c757d',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <div style={{ display: 'flex', gap: '0.25rem', justifyContent: 'center' }}>
                                    <button
                                      onClick={() => navigate(`/edit-pick/${pick.id}`)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#007bff',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      ✏️ Edit
                                    </button>
                                    <button
                                      onClick={() => setDeleteConfirm(pick.id)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#dc3545',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      🗑️ Delete
                                    </button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* ATTS Picks */}
                {game.atts_picks.length > 0 && (
                  <div>
                    <h4 style={{ margin: '0 0 0.75rem 0', color: '#17a2b8' }}>⚡ Anytime TD Picks</h4>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                        <thead>
                          <tr style={{ borderBottom: '2px solid #ddd', background: '#f8f9fa' }}>
                            <th style={{ padding: '0.5rem', textAlign: 'left' }}>User</th>
                            <th style={{ padding: '0.5rem', textAlign: 'left' }}>Player</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Pos</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Odds</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Stake</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Result</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Payout</th>
                            <th style={{ padding: '0.5rem', textAlign: 'center' }}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {game.atts_picks.map(pick => (
                            <tr key={pick.id} style={{ borderBottom: '1px solid #ddd' }}>
                              <td style={{ padding: '0.5rem' }}>{pick.username}</td>
                              <td style={{ padding: '0.5rem', fontWeight: 'bold' }}>{pick.player_name}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{pick.player_position}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{formatOdds(pick.odds)}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>${pick.stake.toFixed(2)}</td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>{getResultBadge(pick.result)}</td>
                              <td style={{ 
                                padding: '0.5rem', 
                                textAlign: 'center',
                                color: pick.payout >= 0 ? '#28a745' : '#dc3545',
                                fontWeight: 'bold'
                              }}>
                                {formatPayout(pick.payout)}
                              </td>
                              <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                {deleteConfirm === pick.id ? (
                                  <div style={{ display: 'flex', gap: '0.25rem', justifyContent: 'center' }}>
                                    <button
                                      onClick={() => handleDeletePick(pick.id)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#dc3545',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      Confirm
                                    </button>
                                    <button
                                      onClick={() => setDeleteConfirm(null)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#6c757d',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <div style={{ display: 'flex', gap: '0.25rem', justifyContent: 'center' }}>
                                    <button
                                      onClick={() => navigate(`/edit-pick/${pick.id}`)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#007bff',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      ✏️ Edit
                                    </button>
                                    <button
                                      onClick={() => setDeleteConfirm(pick.id)}
                                      style={{
                                        padding: '0.25rem 0.5rem',
                                        background: '#dc3545',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      🗑️ Delete
                                    </button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {game.ftd_picks.length === 0 && game.atts_picks.length === 0 && (
                  <div style={{ padding: '1rem', textAlign: 'center', color: '#6c757d', background: '#f8f9fa', borderRadius: '4px' }}>
                    No picks for this game yet
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {!loading && !error && games.length === 0 && (
        <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>
          <p>No games found for Week {week} of the {season} season.</p>
        </div>
      )}
    </div>
  );
};

export default WeekDetail;
