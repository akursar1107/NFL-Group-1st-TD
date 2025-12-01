import React, { useEffect, useState } from 'react';
import { fetchAnalysis } from '../api/analysis';

// Helper for cell color
function getCellColor(rank: number): string {
  if (typeof rank !== 'number') return 'none';
  if (rank <= 10) return '#d4edda'; // Green
  if (rank <= 22) return '#fff3cd'; // Yellow
  return '#f8d7da'; // Red
}


const TABS = [
  { key: 'player', label: 'Player Research' },
  { key: 'team', label: 'Team Analysis' },
  { key: 'defense', label: 'Defense Analysis' },
  { key: 'trends', label: 'Trends & Insights' },
  { key: 'history', label: 'History' },
];

const Analysis: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playerData, setPlayerData] = useState<any[]>([]);
  const [defenseData, setDefenseData] = useState<any | null>(null);
  const [teamData, setTeamData] = useState<any[]>([]);
  const [trendsData, setTrendsData] = useState<any | null>(null);
  const [historyData, setHistoryData] = useState<any | null>(null);
  const [historySeason, setHistorySeason] = useState('2025');
  const [historyWeek, setHistoryWeek] = useState('all');
  const [historyTeam, setHistoryTeam] = useState('all');
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [historyLoading, setHistoryLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('player');
  const [search, setSearch] = useState('');
  const [position, setPosition] = useState('all');
  const [team, setTeam] = useState('all');
  const [timeRange, setTimeRange] = useState('full');

  useEffect(() => {
    fetchAnalysis()
      .then(data => {
        setPlayerData(data.player_data || []);
        setDefenseData(data.defense_data || null);
        setTeamData(data.team_data || []);
        setTrendsData(data.trends_data || null);
        setHistoryData(data.history_data || null);
        setError(data.error || null);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Filter logic for player table
  const filteredPlayers = playerData.filter(p => {
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (position !== 'all' && p.position !== position) return false;
    if (team !== 'all' && p.team !== team) return false;
    return true;
  });

  return (
    <div>
      <h1>Analysis</h1>
      <div style={{ marginBottom: '1rem', borderBottom: '1px solid #ccc' }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '0.5rem 1rem',
              marginRight: '0.5rem',
              border: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #007bff' : '2px solid transparent',
              background: 'none',
              fontWeight: activeTab === tab.key ? 'bold' : 'normal',
              color: activeTab === tab.key ? '#007bff' : '#333',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {loading && <p>Loading analysis...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {!loading && !error && activeTab === 'player' && (
        <>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="Search by player name..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ padding: '0.5rem', flex: 1 }}
            />
            <select value={position} onChange={e => setPosition(e.target.value)} style={{ padding: '0.5rem' }}>
              <option value="all">All Positions</option>
              <option value="QB">QB</option>
              <option value="RB">RB</option>
              <option value="WR">WR</option>
              <option value="TE">TE</option>
              <option value="D/ST">D/ST</option>
            </select>
            <select value={team} onChange={e => setTeam(e.target.value)} style={{ padding: '0.5rem' }}>
              <option value="all">All Teams</option>
              {Array.from(new Set(playerData.map(p => p.team).filter(Boolean))).sort().map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <select value={timeRange} onChange={e => setTimeRange(e.target.value)} style={{ padding: '0.5rem' }}>
              <option value="full">Full Season Stats</option>
              <option value="recent">Last 5 Games Stats</option>
            </select>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Team</th>
                <th>Position</th>
                <th>Form</th>
                <th>Season FTDs</th>
              </tr>
            </thead>
            <tbody>
              {filteredPlayers.map((p, idx) => (
                <tr key={p.name || idx}>
                  <td>{p.name}</td>
                  <td>{p.team}</td>
                  <td>{p.position}</td>
                  <td>{timeRange === 'full' ? (p.stats_full?.form ?? '-') : (p.stats_recent?.form ?? '-')}</td>
                  <td>{timeRange === 'full' ? (p.stats_full?.first_tds ?? '-') : (p.stats_recent?.first_tds ?? '-')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px' }}>
            <strong>Understanding the Stats:</strong>
            <ul>
              <li><strong>Form:</strong> First TDs scored / Games played (toggle between Last 5 Games or Full Season)</li>
              <li><strong>Season FTDs:</strong> Total first touchdown scores this season</li>
              <li><strong>Game Type Filter:</strong> "Standalone Games Only" shows only primetime games</li>
            </ul>
          </div>
        </>
      )}
      {activeTab === 'team' && !loading && !error && (
        <>
          <h2>Team Leaderboard</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Team</th>
                <th>Games</th>
                <th>First TDs</th>
                <th>Success %</th>
                <th>Home FTD%</th>
                <th>Away FTD%</th>
                <th>H/A Diff</th>
              </tr>
            </thead>
            <tbody>
              {teamData.map((team, idx) => (
                <tr key={team.team || idx}>
                  <td>{idx + 1}</td>
                  <td>{team.team}</td>
                  <td>{team.games}</td>
                  <td>{team.first_tds}</td>
                  <td>{team.success_pct ? `${(team.success_pct * 100).toFixed(1)}%` : '-'}</td>
                  <td>{team.home_ftd_pct ? `${(team.home_ftd_pct * 100).toFixed(1)}%` : '-'}</td>
                  <td>{team.away_ftd_pct ? `${(team.away_ftd_pct * 100).toFixed(1)}%` : '-'}</td>
                  <td>{team.ha_diff ? `${(team.ha_diff * 100).toFixed(1)}%` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px' }}>
            <strong>Team Analysis Insights:</strong>
            <ul>
              <li><strong>Success %:</strong> First TDs / Games played</li>
              <li><strong>Home/Away FTD%:</strong> First TD rate in home vs away games</li>
              <li><strong>H/A Diff:</strong> Difference between home and away FTD rates</li>
            </ul>
          </div>
        </>
      )}
      {activeTab === 'defense' && !loading && !error && defenseData && (
        <>
          <h2>Defense vs Position Rankings</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>Defense</th>
                <th>QB</th>
                <th>RB</th>
                <th>WR</th>
                <th>TE</th>
                <th>Funnel Type</th>
              </tr>
            </thead>
            <tbody>
              {(Array.isArray(defenseData) ? defenseData : defenseData.rankings || []).map((def: any, idx: number) => (
                <tr key={def.defense || idx}>
                  <td>{def.defense}</td>
                  <td style={{ background: getCellColor(def.qb_rank) }}>{def.qb_rank}</td>
                  <td style={{ background: getCellColor(def.rb_rank) }}>{def.rb_rank}</td>
                  <td style={{ background: getCellColor(def.wr_rank) }}>{def.wr_rank}</td>
                  <td style={{ background: getCellColor(def.te_rank) }}>{def.te_rank}</td>
                  <td>{def.funnel_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px' }}>
            <strong>Legend:</strong>
            <ul>
              <li><span style={{ background: '#d4edda', padding: '0.2em 0.5em', borderRadius: '2px' }}>Green</span>: Top 10 vs position</li>
              <li><span style={{ background: '#fff3cd', padding: '0.2em 0.5em', borderRadius: '2px' }}>Yellow</span>: Middle 12</li>
              <li><span style={{ background: '#f8d7da', padding: '0.2em 0.5em', borderRadius: '2px' }}>Red</span>: Bottom 10</li>
              <li><strong>Funnel Type:</strong> Indicates which position the defense is weakest against</li>
            </ul>
          </div>
        </>
      )}
      {activeTab === 'trends' && !loading && !error && trendsData && (
        <>
          <h2>Hot Players (Last 5 Games)</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '2rem' }}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Team</th>
                <th>Position</th>
                <th>First TDs (Last 5)</th>
              </tr>
            </thead>
            <tbody>
              {trendsData.hot_players?.map((p: any, idx: number) => (
                <tr key={idx}>
                  <td>{p.name}</td>
                  <td>{p.team}</td>
                  <td>{p.position}</td>
                  <td>{p.first_tds}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <h2>Weekly First TD Scorers</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th>Week</th>
                <th>Player</th>
                <th>Team</th>
                <th>Position</th>
              </tr>
            </thead>
            <tbody>
              {trendsData.weekly_scorers?.map((w: any, idx: number) => (
                <tr key={idx}>
                  <td>{w.week}</td>
                  <td>{w.player}</td>
                  <td>{w.team}</td>
                  <td>{w.position}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px' }}>
            <strong>Usage Tips:</strong>
            <ul>
              <li>Hot players are those with multiple first TDs in recent games.</li>
              <li>Weekly scorers show who scored first TD each week.</li>
            </ul>
          </div>
        </>
      )}
      {activeTab === 'history' && !loading && !error && (
        <>
          <h2>Historical First TD Results</h2>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <select value={historySeason} onChange={e => setHistorySeason(e.target.value)} style={{ padding: '0.5rem' }}>
              {/* Example: seasons 2023-2025 */}
              <option value="2023">2023</option>
              <option value="2024">2024</option>
              <option value="2025">2025</option>
            </select>
            <select value={historyWeek} onChange={e => setHistoryWeek(e.target.value)} style={{ padding: '0.5rem' }}>
              <option value="all">All Weeks</option>
              {[...Array(18)].map((_, i) => (
                <option key={i + 1} value={i + 1}>Week {i + 1}</option>
              ))}
            </select>
            <select value={historyTeam} onChange={e => setHistoryTeam(e.target.value)} style={{ padding: '0.5rem' }}>
              <option value="all">All Teams</option>
              {historyData?.teams?.map((t: string) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          {historyLoading && <p>Loading history...</p>}
          {!historyLoading && historyData?.results && (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th>Season</th>
                  <th>Week</th>
                  <th>Team</th>
                  <th>Player</th>
                  <th>Position</th>
                </tr>
              </thead>
              <tbody>
                {historyData.results
                  .filter((r: any) =>
                    (historySeason === 'all' || r.season === parseInt(historySeason)) &&
                    (historyWeek === 'all' || r.week === parseInt(historyWeek)) &&
                    (historyTeam === 'all' || r.team === historyTeam)
                  )
                  .map((r: any, idx: number) => (
                    <tr key={idx}>
                      <td>{r.season}</td>
                      <td>{r.week}</td>
                      <td>{r.team}</td>
                      <td>{r.player}</td>
                      <td>{r.position}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
};

export default Analysis;

