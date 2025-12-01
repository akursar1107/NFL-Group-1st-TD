import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchStandings, StandingData, StandingsStats } from '../api/standings';

const Standings: React.FC = () => {
  const [standings, setStandings] = useState<StandingData[]>([]);
  const [stats, setStats] = useState<StandingsStats | null>(null);
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStandings();
  }, [season]);

  const loadStandings = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStandings(season);
      setStandings(data.standings);
      setStats(data.stats);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>{season} Season Standings</h2>
        <select 
          value={season} 
          onChange={(e) => setSeason(Number(e.target.value))}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
        >
          <option value={2023}>2023 Season</option>
          <option value={2024}>2024 Season</option>
          <option value={2025}>2025 Season</option>
        </select>
      </div>

      {loading && <p>Loading standings...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}

      {!loading && !error && standings.length > 0 && (
        <>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '2rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ddd', background: '#f8f9fa' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Rank</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Player</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>FTD Record</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>FTD Bankroll</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>ATTS Record</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>ATTS Bankroll</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Total Picks</th>
                </tr>
              </thead>
              <tbody>
                {standings.map((standing, idx) => (
                  <tr key={standing.user_id} style={{ borderBottom: '1px solid #ddd' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{idx + 1}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <Link 
                        to={`/user/${standing.user_id}`}
                        style={{ 
                          color: '#007bff', 
                          textDecoration: 'none',
                          fontWeight: '500'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                        onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                      >
                        {standing.display_name}
                      </Link>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      <span style={{ padding: '0.25rem 0.5rem', background: '#d4edda', borderRadius: '4px', marginRight: '0.25rem' }}>
                        {standing.ftd_wins}W
                      </span>
                      <span style={{ padding: '0.25rem 0.5rem', background: '#f8d7da', borderRadius: '4px', marginRight: '0.25rem' }}>
                        {standing.ftd_losses}L
                      </span>
                      {standing.ftd_pending > 0 && (
                        <span style={{ padding: '0.25rem 0.5rem', background: '#e2e3e5', borderRadius: '4px' }}>
                          {standing.ftd_pending}P
                        </span>
                      )}
                    </td>
                    <td style={{ 
                      padding: '0.75rem', 
                      textAlign: 'center', 
                      fontWeight: 'bold',
                      color: standing.ftd_bankroll > 0 ? '#28a745' : standing.ftd_bankroll < 0 ? '#dc3545' : '#000'
                    }}>
                      {standing.ftd_bankroll.toFixed(2)}u
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      {standing.atts_wins + standing.atts_losses + standing.atts_pending > 0 ? (
                        <>
                          <span style={{ padding: '0.25rem 0.5rem', background: '#d4edda', borderRadius: '4px', marginRight: '0.25rem' }}>
                            {standing.atts_wins}W
                          </span>
                          <span style={{ padding: '0.25rem 0.5rem', background: '#f8d7da', borderRadius: '4px', marginRight: '0.25rem' }}>
                            {standing.atts_losses}L
                          </span>
                          {standing.atts_pending > 0 && (
                            <span style={{ padding: '0.25rem 0.5rem', background: '#e2e3e5', borderRadius: '4px' }}>
                              {standing.atts_pending}P
                            </span>
                          )}
                        </>
                      ) : (
                        <span style={{ color: '#6c757d' }}>-</span>
                      )}
                    </td>
                    <td style={{ 
                      padding: '0.75rem', 
                      textAlign: 'center', 
                      fontWeight: 'bold',
                      color: standing.atts_bankroll > 0 ? '#28a745' : standing.atts_bankroll < 0 ? '#dc3545' : '#6c757d'
                    }}>
                      {standing.atts_wins + standing.atts_losses + standing.atts_pending > 0 
                        ? `${standing.atts_bankroll.toFixed(2)}u` 
                        : '-'}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>{standing.total_picks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {stats && (
            <div>
              <h4>Quick Stats</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem' }}>{stats.total_players}</h5>
                  <p style={{ margin: 0, color: '#6c757d' }}>Players</p>
                </div>
                <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem' }}>{stats.total_ftd_picks}</h5>
                  <p style={{ margin: 0, color: '#6c757d' }}>FTD Picks</p>
                </div>
                <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem' }}>{stats.total_wins}</h5>
                  <p style={{ margin: 0, color: '#6c757d' }}>Total Wins</p>
                </div>
                <div style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '8px', textAlign: 'center' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem' }}>{stats.win_rate.toFixed(1)}%</h5>
                  <p style={{ margin: 0, color: '#6c757d' }}>Win Rate</p>
                </div>
                <div style={{ background: '#d4edda', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #c3e6cb' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#28a745' }}>
                    {stats.league_total_bankroll.toFixed(2)}u
                  </h5>
                  <p style={{ margin: 0, color: '#155724' }}>League Total Bankroll</p>
                </div>
                <div style={{ background: '#cce5ff', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #b8daff' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#004085' }}>
                    {stats.league_ftd_bankroll.toFixed(2)}u
                  </h5>
                  <p style={{ margin: 0, color: '#004085' }}>League FTD Bankroll</p>
                </div>
                <div style={{ background: '#fff3cd', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #ffeeba' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#856404' }}>
                    {stats.league_atts_bankroll.toFixed(2)}u
                  </h5>
                  <p style={{ margin: 0, color: '#856404' }}>League ATTS Bankroll</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {!loading && !error && standings.length === 0 && (
        <p style={{ color: '#6c757d' }}>No standings data available for this season.</p>
      )}
    </div>
  );
};

export default Standings;
