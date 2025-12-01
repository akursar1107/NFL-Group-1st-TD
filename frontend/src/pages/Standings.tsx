import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchStandings, StandingData, StandingsStats } from '../api/standings';

const Standings: React.FC = () => {
  const [standings, setStandings] = useState<StandingData[]>([]);
  const [stats, setStats] = useState<StandingsStats | null>(null);
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc' | 'desc'} | null>({ key: 'total_bankroll', direction: 'desc' });

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const sortedStandings = React.useMemo(() => {
    if (!sortConfig) return standings;
    
    const sorted = [...standings].sort((a, b) => {
      let aValue: number, bValue: number;
      
      if (sortConfig.key === 'ftd_bankroll') {
        aValue = a.ftd_bankroll;
        bValue = b.ftd_bankroll;
      } else if (sortConfig.key === 'atts_bankroll') {
        aValue = a.atts_bankroll;
        bValue = b.atts_bankroll;
      } else if (sortConfig.key === 'total_bankroll') {
        aValue = a.ftd_bankroll + a.atts_bankroll;
        bValue = b.ftd_bankroll + b.atts_bankroll;
      } else {
        return 0;
      }
      
      return sortConfig.direction === 'desc' 
        ? bValue - aValue
        : aValue - bValue;
    });
    
    return sorted;
  }, [standings, sortConfig]);

  const SortIcon: React.FC<{ columnKey: string }> = ({ columnKey }) => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return <span style={{ marginLeft: '0.25rem', opacity: 0.3 }}>↕</span>;
    }
    return <span style={{ marginLeft: '0.25rem' }}>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>;
  };

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
                <tr style={{ borderBottom: '2px solid #ddd', background: '#2c3e50' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: '#fff' }}>Rank</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: '#fff' }}>Player</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center', color: '#fff' }}>FTD Record</th>
                  <th 
                    onClick={() => handleSort('ftd_bankroll')} 
                    style={{ padding: '0.75rem', textAlign: 'center', color: '#fff', cursor: 'pointer', userSelect: 'none' }}
                  >
                    FTD Bankroll<SortIcon columnKey="ftd_bankroll" />
                  </th>
                  <th style={{ padding: '0.75rem', textAlign: 'center', color: '#fff' }}>ATTS Record</th>
                  <th 
                    onClick={() => handleSort('atts_bankroll')} 
                    style={{ padding: '0.75rem', textAlign: 'center', color: '#fff', cursor: 'pointer', userSelect: 'none' }}
                  >
                    ATTS Bankroll<SortIcon columnKey="atts_bankroll" />
                  </th>
                  <th 
                    onClick={() => handleSort('total_bankroll')} 
                    style={{ padding: '0.75rem', textAlign: 'center', color: '#fff', cursor: 'pointer', userSelect: 'none' }}
                  >
                    Total Bankroll<SortIcon columnKey="total_bankroll" />
                  </th>
                  <th style={{ padding: '0.75rem', textAlign: 'center', color: '#fff' }}>Total Picks</th>
                </tr>
              </thead>
              <tbody>
                {sortedStandings.map((standing, idx) => {
                  const totalBankroll = standing.ftd_bankroll + standing.atts_bankroll;
                  return (
                  <tr key={standing.user_id} style={{ borderBottom: '1px solid #4a4a4a', background: '#2a2a2a' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#e0e0e0' }}>{idx + 1}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <Link 
                        to={`/user/${standing.user_id}`}
                        style={{ 
                          color: '#b09613', 
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
                      <span style={{ padding: '0.25rem 0.5rem', background: '#13b047', color: '#fff', borderRadius: '4px', marginRight: '0.25rem', fontWeight: 'bold' }}>
                        {standing.ftd_wins}W
                      </span>
                      <span style={{ padding: '0.25rem 0.5rem', background: '#dc3545', color: '#fff', borderRadius: '4px', marginRight: '0.25rem', fontWeight: 'bold' }}>
                        {standing.ftd_losses}L
                      </span>
                      {standing.ftd_pending > 0 && (
                        <span style={{ padding: '0.25rem 0.5rem', background: '#6c757d', color: '#fff', borderRadius: '4px', fontWeight: 'bold' }}>
                          {standing.ftd_pending}P
                        </span>
                      )}
                    </td>
                    <td style={{ 
                      padding: '0.75rem', 
                      textAlign: 'center', 
                      fontWeight: 'bold',
                      color: standing.ftd_bankroll > 0 ? '#13b047' : standing.ftd_bankroll < 0 ? '#dc3545' : '#e0e0e0'
                    }}>
                      {standing.ftd_bankroll.toFixed(2)}u
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                      {standing.atts_wins + standing.atts_losses + standing.atts_pending > 0 ? (
                        <>
                          <span style={{ padding: '0.25rem 0.5rem', background: '#13b047', color: '#fff', borderRadius: '4px', marginRight: '0.25rem', fontWeight: 'bold' }}>
                            {standing.atts_wins}W
                          </span>
                          <span style={{ padding: '0.25rem 0.5rem', background: '#dc3545', color: '#fff', borderRadius: '4px', marginRight: '0.25rem', fontWeight: 'bold' }}>
                            {standing.atts_losses}L
                          </span>
                          {standing.atts_pending > 0 && (
                            <span style={{ padding: '0.25rem 0.5rem', background: '#6c757d', color: '#fff', borderRadius: '4px', fontWeight: 'bold' }}>
                              {standing.atts_pending}P
                            </span>
                          )}
                        </>
                      ) : (
                        <span style={{ color: '#999' }}>-</span>
                      )}
                    </td>
                    <td style={{ 
                      padding: '0.75rem', 
                      textAlign: 'center', 
                      fontWeight: 'bold',
                      color: standing.atts_bankroll > 0 ? '#13b047' : standing.atts_bankroll < 0 ? '#dc3545' : '#999'
                    }}>
                      {standing.atts_wins + standing.atts_losses + standing.atts_pending > 0 
                        ? `${standing.atts_bankroll.toFixed(2)}u` 
                        : '-'}
                    </td>
                    <td style={{ 
                      padding: '0.75rem', 
                      textAlign: 'center', 
                      fontWeight: 'bold',
                      color: totalBankroll > 0 ? '#13b047' : totalBankroll < 0 ? '#dc3545' : '#e0e0e0'
                    }}>
                      {totalBankroll.toFixed(2)}u
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center', color: '#e0e0e0' }}>{standing.total_picks}</td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {stats && (
            <div>
              <h4 style={{ color: '#e0e0e0' }}>Quick Stats</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div style={{ background: '#2a2a2a', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #4a4a4a' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#e0e0e0' }}>{stats.total_players}</h5>
                  <p style={{ margin: 0, color: '#999' }}>Players</p>
                </div>
                <div style={{ background: '#2a2a2a', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #4a4a4a' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#e0e0e0' }}>{stats.total_ftd_picks}</h5>
                  <p style={{ margin: 0, color: '#999' }}>FTD Picks</p>
                </div>
                <div style={{ background: '#2a2a2a', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #4a4a4a' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#e0e0e0' }}>{stats.total_wins}</h5>
                  <p style={{ margin: 0, color: '#999' }}>Total Wins</p>
                </div>
                <div style={{ background: '#2a2a2a', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #4a4a4a' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#e0e0e0' }}>{stats.win_rate.toFixed(1)}%</h5>
                  <p style={{ margin: 0, color: '#999' }}>Win Rate</p>
                </div>
                <div style={{ background: '#13b04720', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #13b047' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#13b047' }}>
                    {stats.league_total_bankroll.toFixed(2)}u
                  </h5>
                  <p style={{ margin: 0, color: '#13b047' }}>League Total Bankroll</p>
                </div>
                <div style={{ background: '#0056b320', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #007bff' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#6db3ff' }}>
                    {stats.league_ftd_bankroll.toFixed(2)}u
                  </h5>
                  <p style={{ margin: 0, color: '#6db3ff' }}>League FTD Bankroll</p>
                </div>
                <div style={{ background: '#b0961320', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid #b09613' }}>
                  <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#b09613' }}>
                    {stats.league_atts_bankroll.toFixed(2)}u
                  </h5>
                  <p style={{ margin: 0, color: '#b09613' }}>League ATTS Bankroll</p>
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
