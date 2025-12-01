import React, { useEffect, useState } from 'react';
import { fetchAnalysis } from '../api/analysis';

// Helper for cell color
function getCellColor(rank: number): string {
  if (typeof rank !== 'number') return 'transparent';
  if (rank <= 10) return '#d4edda'; // Green
  if (rank <= 22) return '#fff3cd'; // Yellow
  return '#f8d7da'; // Red
}

// Helper for position badge color
function getPositionColor(position: string): string {
  switch (position) {
    case 'QB': return '#007bff'; // Blue
    case 'RB': return '#28a745'; // Green
    case 'WR': return '#ffc107'; // Yellow/Gold
    case 'TE': return '#17a2b8'; // Cyan
    default: return '#dc3545'; // Red for all others
  }
}


const TABS = [
  { key: 'player', label: 'Player Research', icon: '👤' },
  { key: 'team', label: 'Team Analysis', icon: '🛡️' },
  { key: 'defense', label: 'Defense Analysis', icon: '📊' },
  { key: 'trends', label: 'Trends & Insights', icon: '📈' },
  { key: 'history', label: 'History', icon: '🕐' },
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
  const [sortField, setSortField] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [teamSortField, setTeamSortField] = useState<string>('');
  const [teamSortDirection, setTeamSortDirection] = useState<'asc' | 'desc'>('desc');
  const [defenseSortField, setDefenseSortField] = useState<string>('');
  const [defenseSortDirection, setDefenseSortDirection] = useState<'asc' | 'desc'>('asc');

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

  // Sort handler
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Team sort handler
  const handleTeamSort = (field: string) => {
    if (teamSortField === field) {
      setTeamSortDirection(teamSortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setTeamSortField(field);
      setTeamSortDirection('desc');
    }
  };

  // Defense sort handler
  const handleDefenseSort = (field: string) => {
    if (defenseSortField === field) {
      setDefenseSortDirection(defenseSortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setDefenseSortField(field);
      setDefenseSortDirection('asc'); // Default to asc for defense (lower rank = better defense)
    }
  };

  // Sort filtered players
  const sortedPlayers = [...filteredPlayers].sort((a, b) => {
    if (!sortField) return 0;
    
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    // Handle stats nested in stats_full or stats_recent
    if (sortField === 'form' || sortField === 'first_tds') {
      const statsKey = timeRange === 'full' ? 'stats_full' : 'stats_recent';
      aVal = a[statsKey]?.[sortField];
      bVal = b[statsKey]?.[sortField];
    }
    
    // rz_rate and od_rate are top-level fields
    if (sortField === 'rz_rate' || sortField === 'od_rate') {
      aVal = a[sortField];
      bVal = b[sortField];
    }
    
    // Handle null/undefined values
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    
    // Numeric comparison
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    }
    
    // String comparison
    const aStr = String(aVal).toLowerCase();
    const bStr = String(bVal).toLowerCase();
    if (sortDirection === 'asc') {
      return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
    } else {
      return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
    }
  });

  // Sort team data
  const sortedTeams = [...teamData].sort((a, b) => {
    if (!teamSortField) return 0;
    
    let aVal = a[teamSortField];
    let bVal = b[teamSortField];
    
    // Handle null/undefined values
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    
    // Numeric comparison
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return teamSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    }
    
    // String comparison
    const aStr = String(aVal).toLowerCase();
    const bStr = String(bVal).toLowerCase();
    if (teamSortDirection === 'asc') {
      return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
    } else {
      return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
    }
  });

  // Sort defense data
  const sortedDefense = defenseData ? [...defenseData].sort((a: any, b: any) => {
    if (!defenseSortField) return 0;
    
    let aVal = a[defenseSortField];
    let bVal = b[defenseSortField];
    
    // Handle null/undefined values
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    
    // Numeric comparison
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return defenseSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    }
    
    // String comparison
    const aStr = String(aVal).toLowerCase();
    const bStr = String(bVal).toLowerCase();
    if (defenseSortDirection === 'asc') {
      return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
    } else {
      return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
    }
  }) : [];

  return (
    <div className="container-fluid mt-4">
      <div className="row mb-3">
        <div className="col-12">
          <h1 className="display-5">
            📊 Statistical Analysis
            <small className="text-muted fs-6 ms-2">2025 Season</small>
          </h1>
          <p className="text-muted mb-0">
            🕐 Last updated: {new Date().toLocaleString()} | Current week: 13
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <ul className="nav nav-tabs mb-3" role="tablist">
        {TABS.map(tab => (
          <li key={tab.key} className="nav-item" role="presentation">
            <button
              className={`nav-link ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
              type="button"
              role="tab"
            >
              {tab.icon} {tab.label}
            </button>
          </li>
        ))}
      </ul>

      {loading && <div className="alert alert-info">Loading analysis...</div>}
      {error && <div className="alert alert-danger">❌ {error}</div>}
      {!loading && !error && activeTab === 'player' && (
        <>
          <div className="row mb-3">
            <div className="col-md-3">
              <input
                type="text"
                className="form-control"
                placeholder="Search by player name..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <div className="col-md-2">
              <select className="form-select" value={position} onChange={e => setPosition(e.target.value)}>
                <option value="all">All Positions</option>
                <option value="QB">QB</option>
                <option value="RB">RB</option>
                <option value="WR">WR</option>
                <option value="TE">TE</option>
                <option value="D/ST">D/ST</option>
              </select>
            </div>
            <div className="col-md-2">
              <select className="form-select" value={team} onChange={e => setTeam(e.target.value)}>
                <option value="all">All Teams</option>
                {Array.from(new Set(playerData.map(p => p.team).filter(Boolean))).sort().map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <select className="form-select" value={timeRange} onChange={e => setTimeRange(e.target.value)}>
                <option value="full">Full Season Stats</option>
                <option value="recent">Last 5 Games Stats</option>
              </select>
            </div>
            <div className="col-md-3 text-end">
              <small className="text-muted">{sortedPlayers.length} players tracked</small>
            </div>
          </div>
          <div className="table-responsive">
            <table className="table table-striped table-hover">
              <thead className="table-dark">
                <tr>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('name')}>
                    Name {sortField === 'name' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('team')}>
                    Team {sortField === 'team' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('position')}>
                    Position {sortField === 'position' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('form')}>
                    Form {sortField === 'form' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('first_tds')}>
                    Season FTDs {sortField === 'first_tds' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('rz_rate')}>
                    RZ Rate {sortField === 'rz_rate' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('od_rate')}>
                    OD Rate {sortField === 'od_rate' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedPlayers.map((p, idx) => (
                  <tr key={p.name || idx}>
                    <td><strong>{p.name}</strong></td>
                    <td>{p.team}</td>
                    <td>
                      <span 
                        className="badge" 
                        style={{ backgroundColor: getPositionColor(p.position), color: 'white' }}
                      >
                        {p.position}
                      </span>
                    </td>
                    <td>{timeRange === 'full' ? (p.stats_full?.form ?? '-') : (p.stats_recent?.form ?? '-')}</td>
                    <td><strong>{timeRange === 'full' ? (p.stats_full?.first_tds ?? '-') : (p.stats_recent?.first_tds ?? '-')}</strong></td>
                    <td>
                      {p.rz_rate > 0 ? (
                        <span title={`${p.rz_tds}/${p.rz_opps} TDs/Opps`}>
                          {p.rz_rate.toFixed(1)}%
                        </span>
                      ) : '-'}
                    </td>
                    <td>
                      {p.od_rate > 0 ? (
                        <span title={`${p.od_tds}/${p.od_opps} TDs/Opps`}>
                          {p.od_rate.toFixed(1)}%
                        </span>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="alert alert-info mt-3">
            <strong>ℹ️ Understanding the Stats:</strong>
            <ul className="mb-0 mt-2">
              <li><strong>Form:</strong> First TDs scored / Games played (toggle between Last 5 Games or Full Season using the dropdown)</li>
              <li><strong>Season FTDs:</strong> Total first touchdown scores this season (filters by game type when "Standalone Games Only" selected)</li>
              <li><strong>RZ Rate:</strong> Red zone touchdown conversion rate (hover for TDs/Opportunities)</li>
              <li><strong>OD Rate:</strong> Opening drive touchdown conversion rate (hover for TDs/Opportunities)</li>
            </ul>
          </div>
        </>
      )}
      {activeTab === 'team' && !loading && !error && (
        <>
          <h2 className="mb-3">Team Leaderboard</h2>
          <div className="table-responsive">
            <table className="table table-striped table-hover">
              <thead className="table-dark">
                <tr>
                  <th>Rank</th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('team')}>
                    Team {teamSortField === 'team' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('games')}>
                    Games {teamSortField === 'games' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('first_tds')}>
                    First TDs {teamSortField === 'first_tds' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('success_pct')}>
                    Success % {teamSortField === 'success_pct' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('home_ftd_pct')}>
                    Home FTD% {teamSortField === 'home_ftd_pct' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('away_ftd_pct')}>
                    Away FTD% {teamSortField === 'away_ftd_pct' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('ha_diff')}>
                    H/A Diff {teamSortField === 'ha_diff' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('rz_pass_pct')}>
                    RZ Pass% {teamSortField === 'rz_pass_pct' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleTeamSort('rz_run_pct')}>
                    RZ Run% {teamSortField === 'rz_run_pct' && (teamSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedTeams.map((team, idx) => {
                  const haDiffValue = team.ha_diff != null ? team.ha_diff.toFixed(1) : null;
                  const haDiffDisplay = haDiffValue ? `${parseFloat(haDiffValue) > 0 ? '+' : ''}${haDiffValue}%` : '-';
                  
                  return (
                    <tr key={team.team || idx}>
                      <td><strong>{idx + 1}</strong></td>
                      <td><strong>{team.team}</strong></td>
                      <td>{team.games}</td>
                      <td><strong>{team.first_tds}</strong></td>
                      <td>{team.success_pct != null ? `${team.success_pct.toFixed(1)}%` : '-'}</td>
                      <td>{team.home_ftd_pct != null ? `${team.home_ftd_pct.toFixed(1)}%` : '-'}</td>
                      <td>{team.away_ftd_pct != null ? `${team.away_ftd_pct.toFixed(1)}%` : '-'}</td>
                      <td>{haDiffDisplay}</td>
                      <td>{team.rz_pass_pct != null ? `${team.rz_pass_pct.toFixed(1)}%` : '-'}</td>
                      <td>{team.rz_run_pct != null ? `${team.rz_run_pct.toFixed(1)}%` : '-'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="alert alert-info mt-3">
            <strong>Team Analysis Insights:</strong>
            <ul className="mb-0 mt-2">
              <li><strong>Success %:</strong> First TDs / Games played</li>
              <li><strong>Home/Away FTD%:</strong> First TD rate in home vs away games</li>
              <li><strong>H/A Diff:</strong> Difference between home and away FTD rates (positive = better at home)</li>
              <li><strong>RZ Pass%:</strong> Red zone pass play percentage (higher = pass-heavy in RZ)</li>
              <li><strong>RZ Run%:</strong> Red zone run play percentage (higher = run-heavy in RZ)</li>
            </ul>
          </div>
        </>
      )}
      {activeTab === 'defense' && !loading && !error && defenseData && (
        <>
          <h2 className="mb-3">Defense vs Position Rankings</h2>
          <p className="text-muted">Lower rank = tougher defense against that position (harder matchup for FTD)</p>
          <div className="table-responsive">
            <table className="table table-sm table-bordered">
              <thead className="table-dark">
                <tr>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleDefenseSort('defense')}>
                    Defense {defenseSortField === 'defense' && (defenseSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th className="text-center" style={{ cursor: 'pointer' }} onClick={() => handleDefenseSort('qb_rank')}>
                    QB {defenseSortField === 'qb_rank' && (defenseSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th className="text-center" style={{ cursor: 'pointer' }} onClick={() => handleDefenseSort('rb_rank')}>
                    RB {defenseSortField === 'rb_rank' && (defenseSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th className="text-center" style={{ cursor: 'pointer' }} onClick={() => handleDefenseSort('wr_rank')}>
                    WR {defenseSortField === 'wr_rank' && (defenseSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th className="text-center" style={{ cursor: 'pointer' }} onClick={() => handleDefenseSort('te_rank')}>
                    TE {defenseSortField === 'te_rank' && (defenseSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleDefenseSort('avg_rank')}>
                    Avg Rank {defenseSortField === 'avg_rank' && (defenseSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleDefenseSort('funnel_type')}>
                    Funnel Type {defenseSortField === 'funnel_type' && (defenseSortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedDefense.map((def: any, idx: number) => (
                  <tr key={def.defense || idx}>
                    <td><strong>{def.defense}</strong></td>
                    <td className="text-center" style={{ backgroundColor: getCellColor(def.qb_rank) }}>{def.qb_rank}</td>
                    <td className="text-center" style={{ backgroundColor: getCellColor(def.rb_rank) }}>{def.rb_rank}</td>
                    <td className="text-center" style={{ backgroundColor: getCellColor(def.wr_rank) }}>{def.wr_rank}</td>
                    <td className="text-center" style={{ backgroundColor: getCellColor(def.te_rank) }}>{def.te_rank}</td>
                    <td className="text-center">
                      {def.avg_rank ? def.avg_rank.toFixed(1) : ((def.qb_rank + def.rb_rank + def.wr_rank + def.te_rank) / 4).toFixed(1)}
                    </td>
                    <td>
                      {def.funnel_type && def.funnel_type !== 'Balanced' && def.funnel_type !== 'None' ? (
                        <span className="badge bg-warning text-dark">{def.funnel_type}</span>
                      ) : (
                        <span className="text-muted">Balanced</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="alert alert-info mt-3">
            <strong>Legend:</strong>
            <div className="row mt-2">
              <div className="col-md-4">
                <span className="badge" style={{ backgroundColor: '#d4edda', color: '#155724', padding: '0.5em 1em' }}>Green</span>
                <span className="ms-2">Top 10 vs position</span>
              </div>
              <div className="col-md-4">
                <span className="badge" style={{ backgroundColor: '#fff3cd', color: '#856404', padding: '0.5em 1em' }}>Yellow</span>
                <span className="ms-2">Middle 12</span>
              </div>
              <div className="col-md-4">
                <span className="badge" style={{ backgroundColor: '#f8d7da', color: '#721c24', padding: '0.5em 1em' }}>Red</span>
                <span className="ms-2">Bottom 10</span>
              </div>
            </div>
            <hr />
            <p className="mb-0"><strong>Funnel Type:</strong> Indicates which position the defense is weakest against (best FTD targets)</p>
          </div>
        </>
      )}
      {activeTab === 'trends' && !loading && !error && trendsData && (
        <>
          <h2 className="mb-3">🔥 Hot Players (Last 5 Games)</h2>
          <p className="text-muted">Players with 2+ First TDs in their last 5 games</p>
          <div className="table-responsive">
            <table className="table table-striped table-hover mb-4">
              <thead className="table-dark">
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
                    <td><strong>{p.name}</strong></td>
                    <td>{p.team}</td>
                    <td><span className="badge bg-secondary">{p.position}</span></td>
                    <td><strong className="text-success">{p.first_tds}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 className="mb-3 mt-5">📅 Weekly First TD Scorers</h2>
          <div className="table-responsive">
            <table className="table table-sm table-striped">
              <thead className="table-dark">
                <tr>
                  <th>Week</th>
                  <th>Player</th>
                  <th>Team</th>
                  <th>Position</th>
                </tr>
              </thead>
              <tbody>
                {trendsData.weekly_scorers?.slice().reverse().slice(0, 50).map((s: any, idx: number) => (
                  <tr key={idx}>
                    <td><span className="badge bg-primary">{s.week}</span></td>
                    <td><strong>{s.player}</strong></td>
                    <td>{s.team}</td>
                    <td><span className="badge bg-secondary">{s.position}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {activeTab === 'history' && !loading && !error && (
        <>
          <h2 className="mb-3">📜 Historical First TD Results</h2>
          <div className="row mb-3">
            <div className="col-md-3">
              <select className="form-select" value={historySeason} onChange={e => setHistorySeason(e.target.value)}>
                <option value="2023">2023</option>
                <option value="2024">2024</option>
                <option value="2025">2025</option>
              </select>
            </div>
            <div className="col-md-3">
              <select className="form-select" value={historyWeek} onChange={e => setHistoryWeek(e.target.value)}>
                <option value="all">All Weeks</option>
                {[...Array(18)].map((_, i) => (
                  <option key={i + 1} value={i + 1}>Week {i + 1}</option>
                ))}
              </select>
            </div>
            <div className="col-md-3">
              <select className="form-select" value={historyTeam} onChange={e => setHistoryTeam(e.target.value)}>
                <option value="all">All Teams</option>
                {historyData?.teams?.map((t: string) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>
          {historyLoading && <div className="alert alert-info">Loading history...</div>}
          {!historyLoading && historyData?.results && (
            <div className="table-responsive">
              <table className="table table-striped table-hover">
                <thead className="table-dark">
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
                        <td><span className="badge bg-primary">{r.week}</span></td>
                        <td><strong>{r.team}</strong></td>
                        <td><strong>{r.player}</strong></td>
                        <td>
                          <span 
                            className="badge" 
                            style={{ backgroundColor: getPositionColor(r.position), color: 'white' }}
                          >
                            {r.position || 'N/A'}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
          {!historyLoading && !historyData && (
            <div className="alert alert-warning">No historical data available yet.</div>
          )}
        </>
      )}
    </div>
  );
};

export default Analysis;

