import React, { useEffect, useState } from 'react';
import { fetchBestBets, BetData } from '../api/bestBets';

const BestBets: React.FC = () => {
  const [bets, setBets] = useState<BetData[]>([]);
  const [season, setSeason] = useState(2025);
  const [week, setWeek] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [minEV, setMinEV] = useState(0);

  useEffect(() => {
    loadBestBets();
  }, [season]);

  const loadBestBets = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchBestBets(season);
      if (data.error) {
        setError(data.error);
        setBets([]);
      } else {
        setBets(data.bets);
        setWeek(data.week);
        setLastUpdated(data.last_updated);
      }
    } catch (err: any) {
      setError(err.message);
      setBets([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredBets = bets.filter(bet => bet.ev >= minEV);

  const getEVClass = (ev: number) => {
    if (ev >= 15) return { background: '#d4edda', color: '#155724' };
    if (ev >= 5) return { background: '#fff3cd', color: '#856404' };
    return { background: '#f8f9fa', color: '#212529' };
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2>💰 Best Bets Scanner</h2>
        <p style={{ color: '#6c757d' }}>
          Positive Expected Value (EV) first touchdown bets for Week {week} - {season} Season
        </p>
        {lastUpdated && (
          <small style={{ color: '#6c757d' }}>
            Last updated: {new Date(lastUpdated).toLocaleString()} | Odds cached for 1 hour
          </small>
        )}
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
          value={minEV} 
          onChange={(e) => setMinEV(Number(e.target.value))}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
        >
          <option value={0}>All Positive EV</option>
          <option value={5}>EV &gt; 5%</option>
          <option value={10}>EV &gt; 10%</option>
          <option value={15}>EV &gt; 15%</option>
        </select>

        <button 
          onClick={loadBestBets}
          style={{ 
            padding: '0.5rem 1rem', 
            background: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: 'pointer' 
          }}
        >
          🔄 Refresh Odds
        </button>
      </div>

      {loading && <p>Loading best bets...</p>}
      {error && (
        <div style={{ padding: '1rem', background: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '1rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {!loading && !error && filteredBets.length > 0 && (
        <>
          <div style={{ marginBottom: '1rem', padding: '1rem', background: '#cce5ff', borderRadius: '4px' }}>
            <strong>Legend:</strong>
            <ul style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem' }}>
              <li><strong>EV (Expected Value):</strong> Higher is better. Positive EV means profitable long-term.</li>
              <li><strong>Kelly %:</strong> Recommended bet size as % of bankroll (conservative).</li>
              <li><strong>Fair Odds:</strong> What the odds should be based on probability.</li>
              <li><strong>Funnel:</strong> Defense weakness indicator (Pass/Run Funnel).</li>
            </ul>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ddd', background: '#f8f9fa' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>Player</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Team</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>vs</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Pos</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Prob %</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Fair Odds</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Best Odds</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Book</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>EV %</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Kelly %</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Form</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>RZ</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>OD</th>
                  <th style={{ padding: '0.75rem', textAlign: 'center' }}>Funnel</th>
                </tr>
              </thead>
              <tbody>
                {filteredBets.map((bet, idx) => {
                  const evStyle = getEVClass(bet.ev);
                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid #ddd', ...evStyle }}>
                      <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>{bet.player}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>{bet.team}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>{bet.opponent}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>{bet.position}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>{bet.prob}%</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>+{bet.fair_odds}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: 'bold' }}>+{bet.best_odds}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center', fontSize: '0.85rem' }}>{bet.sportsbook}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: 'bold' }}>
                        {bet.ev > 0 ? '+' : ''}{bet.ev}%
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>{bet.kelly}%</td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                        {bet.first_tds}/{bet.games}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }} title={`Red Zone: ${bet.rz_tds} TDs / ${bet.rz_opps} opps`}>
                        {bet.rz_tds}/{bet.rz_opps}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }} title={`Opening Drive: ${bet.od_tds} TDs / ${bet.od_opps} opps`}>
                        {bet.od_tds}/{bet.od_opps}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center', fontSize: '0.75rem' }}>
                        {bet.funnel_type ? (
                          <span style={{ 
                            padding: '0.25rem 0.5rem', 
                            background: bet.funnel_type.includes('Pass') ? '#d1ecf1' : '#f8d7da',
                            borderRadius: '4px'
                          }}>
                            {bet.funnel_type}
                          </span>
                        ) : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
            <h4>How to Use This Data</h4>
            <ol style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem' }}>
              <li><strong>Focus on High EV:</strong> Prioritize bets with EV &gt; 10% for best value.</li>
              <li><strong>Check Form:</strong> Players with recent first TDs have momentum.</li>
              <li><strong>Red Zone & Opening Drive:</strong> High efficiency here = higher FTD probability.</li>
              <li><strong>Funnel Defenses:</strong> Pass funnels favor WR/TE, Run funnels favor RB.</li>
              <li><strong>Kelly Criterion:</strong> Suggested bet size - stay disciplined!</li>
            </ol>
          </div>
        </>
      )}

      {!loading && !error && filteredBets.length === 0 && bets.length > 0 && (
        <p style={{ color: '#6c757d' }}>No bets match your filter criteria. Try lowering the minimum EV.</p>
      )}

      {!loading && !error && bets.length === 0 && (
        <p style={{ color: '#6c757d' }}>No positive EV bets found for this week.</p>
      )}
    </div>
  );
};

export default BestBets;
