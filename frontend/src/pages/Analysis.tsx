// ⚠️ REACT VERSION - Uses /api/analysis endpoint (NOT Flask template!)
// ⚠️ API returns percentages as numbers (91.7), NOT decimals (0.917)
// ⚠️ Display as {value}%, do NOT multiply by 100 again!

import React, { useEffect, useState } from 'react';
import { fetchAnalysis } from '../api/analysis';
import {
  colors,
  spacing,
  fontSize,
  fontWeight,
  borderRadius,
  modalStyles,
  tableStyles,
  badgeStyles,
  cardStyles,
  getPositionColor,
  getCellColor,
} from '../styles/commonStyles';
import styles from './Analysis.module.css';


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
  const [selectedPlayer, setSelectedPlayer] = useState<any | null>(null);
  const [selectedDefense, setSelectedDefense] = useState<any | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [historyLoading, setHistoryLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('player');
  const [search, setSearch] = useState('');
  const [position, setPosition] = useState('all');
  const [team, setTeam] = useState('all');
  const [timeRange, setTimeRange] = useState('full');
  
  // Sorting state
  const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc' | 'desc'} | null>(null);

  // Generic sort handler
  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Sort data based on current sort config
  const sortData = (data: any[], currentSortConfig: typeof sortConfig) => {
    if (!currentSortConfig) return data;
    
    const sorted = [...data].sort((a, b) => {
      // Handle nested objects (for player stats) - check FIRST
      let aValue, bValue;
      
      if (currentSortConfig.key.includes('.')) {
        const keys = currentSortConfig.key.split('.');
        aValue = keys.reduce((obj, key) => obj?.[key], a);
        bValue = keys.reduce((obj, key) => obj?.[key], b);
      } else {
        aValue = a[currentSortConfig.key];
        bValue = b[currentSortConfig.key];
      }
      
      // Handle null/undefined
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;
      
      // Compare
      if (typeof aValue === 'string') {
        return currentSortConfig.direction === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      return currentSortConfig.direction === 'asc'
        ? (aValue || 0) - (bValue || 0)
        : (bValue || 0) - (aValue || 0);
    });
    
    return sorted;
  };

  // Sort icon component
  const SortIcon = ({ columnKey }: { columnKey: string }) => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return <span style={{ marginLeft: '5px', opacity: 0.3 }}>↕</span>;
    }
    return <span style={{ marginLeft: '5px' }}>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>;
  };

  useEffect(() => {
    fetchAnalysis()
      .then(data => {
        console.log('Analysis data received:', data);
        setPlayerData(data.player_data || []);
        setDefenseData(data.defense_data || null);
        setTeamData(data.team_data || []);
        setTrendsData(data.trends_data || null);
        setHistoryData(data.history_data || null);
        setError(data.error || null);
        setLoading(false);
      })
      .catch(err => {
        console.error('Analysis fetch error:', err);
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
  
  // Apply sorting to filtered players
  const sortedPlayers = sortData(filteredPlayers, sortConfig);
  
  // Apply sorting to team data
  const sortedTeamData = sortData(teamData, sortConfig);
  
  // Apply sorting to defense data
  const sortedDefenseData = sortData(
    Array.isArray(defenseData) ? defenseData : (defenseData?.rankings || []), 
    sortConfig
  );
  
  // Apply sorting to hot players
  const sortedHotPlayers = sortData(trendsData?.hot_players || [], sortConfig);
  
  // Apply sorting to weekly scorers
  const sortedWeeklyScorers = sortData(trendsData?.weekly_scorers || [], sortConfig);

  return (
    <div>
      <h1>Analysis</h1>
      <div style={{ marginBottom: '1rem', borderBottom: '1px solid #ccc', display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
        {TABS.map(tab => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '0.75rem 1.25rem',
                border: 'none',
                borderBottom: isActive ? '3px solid #007bff' : '3px solid transparent',
                background: isActive ? '#007bff' : '#444',
                fontWeight: isActive ? 'bold' : 'normal',
                color: '#fff',
                cursor: 'pointer',
                borderRadius: '4px 4px 0 0',
                fontSize: '14px',
              }}
            >
              {tab.label}
            </button>
          );
        })}
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
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            border: '1px solid #ddd',
            backgroundColor: '#fff'
          }}>
            <thead>
              <tr style={{ background: '#2c3e50' }}>
                <th onClick={() => handleSort('name')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Name<SortIcon columnKey="name" />
                </th>
                <th onClick={() => handleSort('team')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Team<SortIcon columnKey="team" />
                </th>
                <th onClick={() => handleSort('position')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Position<SortIcon columnKey="position" />
                </th>
                <th onClick={() => handleSort(timeRange === 'full' ? 'stats_full.form' : 'stats_recent.form')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Form<SortIcon columnKey={timeRange === 'full' ? 'stats_full.form' : 'stats_recent.form'} />
                </th>
                <th onClick={() => handleSort(timeRange === 'full' ? 'stats_full.first_tds' : 'stats_recent.first_tds')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Season FTDs<SortIcon columnKey={timeRange === 'full' ? 'stats_full.first_tds' : 'stats_recent.first_tds'} />
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedPlayers.map((p, idx) => (
                <tr key={p.name || idx} style={{ 
                  background: idx % 2 === 0 ? '#fff' : '#f8f9fa',
                  transition: 'background-color 0.2s',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#e3f2fd'}
                onMouseLeave={(e) => e.currentTarget.style.background = idx % 2 === 0 ? '#fff' : '#f8f9fa'}
                onClick={() => setSelectedPlayer(p)}
                >
                  <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{p.name}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{p.team}</td>
                  <td style={{ 
                    padding: '10px', 
                    border: '1px solid #ddd', 
                    color: '#fff',
                    backgroundColor: getPositionColor(p.position),
                    fontWeight: 600,
                    textAlign: 'center'
                  }}>{p.position}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{timeRange === 'full' ? (p.stats_full?.form ?? '-') : (p.stats_recent?.form ?? '-')}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{timeRange === 'full' ? (p.stats_full?.first_tds ?? '-') : (p.stats_recent?.first_tds ?? '-')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px', color: '#333' }}>
            <strong style={{ color: '#333' }}>Understanding the Stats:</strong>
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
          <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ddd', backgroundColor: '#fff' }}>
            <thead>
              <tr style={{ background: '#2c3e50' }}>
                <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff' }}>Rank</th>
                <th onClick={() => handleSort('team')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Team<SortIcon columnKey="team" />
                </th>
                <th onClick={() => handleSort('games')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Games<SortIcon columnKey="games" />
                </th>
                <th onClick={() => handleSort('first_tds')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  First TDs<SortIcon columnKey="first_tds" />
                </th>
                <th onClick={() => handleSort('success_pct')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Success %<SortIcon columnKey="success_pct" />
                </th>
                <th onClick={() => handleSort('home_ftd_pct')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Home FTD%<SortIcon columnKey="home_ftd_pct" />
                </th>
                <th onClick={() => handleSort('away_ftd_pct')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Away FTD%<SortIcon columnKey="away_ftd_pct" />
                </th>
                <th onClick={() => handleSort('ha_diff')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  H/A Diff<SortIcon columnKey="ha_diff" />
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedTeamData.map((team, idx) => (
                <tr key={team.team || idx} style={{ background: idx % 2 === 0 ? '#fff' : '#f8f9fa' }}>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{idx + 1}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{team.team}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{team.games}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{team.first_tds}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{team.success_pct ? `${team.success_pct.toFixed(1)}%` : '-'}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{team.home_ftd_pct ? `${team.home_ftd_pct.toFixed(1)}%` : '-'}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{team.away_ftd_pct ? `${team.away_ftd_pct.toFixed(1)}%` : '-'}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{team.ha_diff ? `${team.ha_diff.toFixed(1)}%` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px', color: '#333' }}>
            <strong style={{ color: '#333' }}>Team Analysis Insights:</strong>
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
          <div style={{ marginBottom: '1rem', background: '#e8f4f8', padding: '1rem', borderRadius: '4px', borderLeft: '4px solid #17a2b8', color: '#333' }}>
            <p style={{ margin: '0 0 0.5rem 0', fontSize: '14px', lineHeight: '1.6', color: '#333' }}>
              <strong style={{ color: '#333' }}>How to read this table:</strong> Lower rankings (1-10) indicate defenses that are more vulnerable to that position, 
              meaning they allow more first touchdowns to that position type. Higher rankings (22-32) indicate stronger defenses against that position. 
              The "Funnel Type" shows which position the defense struggles most against, helping you identify favorable matchups.
            </p>
            <p style={{ margin: 0, fontSize: '13px', fontStyle: 'italic', color: '#555' }}>
              <strong style={{ color: '#333' }}>Example:</strong> If a defense has a WR rank of 3, they're one of the worst defenses against wide receivers 
              (allowing many first TDs to WRs). If their TE rank is 28, they're strong against tight ends (allowing few first TDs to TEs).
            </p>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ddd', backgroundColor: '#fff' }}>
            <thead>
              <tr style={{ background: '#2c3e50' }}>
                <th onClick={() => handleSort('defense')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Defense<SortIcon columnKey="defense" />
                </th>
                <th onClick={() => handleSort('qb_rank')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  QB<SortIcon columnKey="qb_rank" />
                </th>
                <th onClick={() => handleSort('rb_rank')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  RB<SortIcon columnKey="rb_rank" />
                </th>
                <th onClick={() => handleSort('wr_rank')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  WR<SortIcon columnKey="wr_rank" />
                </th>
                <th onClick={() => handleSort('te_rank')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  TE<SortIcon columnKey="te_rank" />
                </th>
                <th onClick={() => handleSort('funnel_type')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Funnel Type<SortIcon columnKey="funnel_type" />
                </th>
                <th onClick={() => handleSort('ftds_allowed.Total')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  FTDs Allowed<SortIcon columnKey="ftds_allowed.Total" />
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedDefenseData.map((def: any, idx: number) => (
                <tr 
                  key={def.defense || idx}
                  style={{
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#e3f2fd'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  onClick={() => setSelectedDefense(def)}
                >
                  <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{def.defense}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', background: getCellColor(def.qb_rank), color: '#333' }}>{def.qb_rank}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', background: getCellColor(def.rb_rank), color: '#333' }}>{def.rb_rank}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', background: getCellColor(def.wr_rank), color: '#333' }}>{def.wr_rank}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', background: getCellColor(def.te_rank), color: '#333' }}>{def.te_rank}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{def.funnel_type}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333', fontWeight: 600 }}>{def.ftds_allowed?.Total || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px', color: '#333' }}>
            <strong style={{ color: '#333' }}>Legend:</strong>
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
          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '2rem', border: '1px solid #ddd', backgroundColor: '#fff' }}>
            <thead>
              <tr style={{ background: '#2c3e50' }}>
                <th onClick={() => handleSort('name')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Name<SortIcon columnKey="name" />
                </th>
                <th onClick={() => handleSort('team')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Team<SortIcon columnKey="team" />
                </th>
                <th onClick={() => handleSort('position')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  Position<SortIcon columnKey="position" />
                </th>
                <th onClick={() => handleSort('first_tds')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                  First TDs (Last 5)<SortIcon columnKey="first_tds" />
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedHotPlayers.map((p: any, idx: number) => (
                <tr 
                  key={idx} 
                  onClick={() => setSelectedPlayer({ name: p.name, team: p.team, position: p.position })}
                  style={{ 
                    background: idx % 2 === 0 ? '#fff' : '#f8f9fa',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#e3f2fd'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = idx % 2 === 0 ? '#fff' : '#f8f9fa'}
                >
                  <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{p.name}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{p.team}</td>
                  <td style={{ 
                    padding: '10px', 
                    border: '1px solid #ddd', 
                    color: '#fff',
                    backgroundColor: getPositionColor(p.position),
                    fontWeight: 600,
                    textAlign: 'center'
                  }}>{p.position}</td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{p.first_tds}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', background: '#f8f9fa', padding: '1rem', borderRadius: '4px', color: '#333' }}>
            <strong style={{ color: '#333' }}>Usage Tips:</strong>
            <ul>
              <li>Hot players are those with multiple first TDs in recent games.</li>
              <li>Click on any player row to see their detailed first TD history.</li>
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
            <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ddd', backgroundColor: '#fff' }}>
              <thead>
                <tr style={{ background: '#2c3e50' }}>
                  <th onClick={() => handleSort('week')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                    Week<SortIcon columnKey="week" />
                  </th>
                  <th onClick={() => handleSort('team')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                    Home Team<SortIcon columnKey="team" />
                  </th>
                  <th onClick={() => handleSort('opponent')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                    Away Team<SortIcon columnKey="opponent" />
                  </th>
                  <th onClick={() => handleSort('is_standalone')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                    Game Type<SortIcon columnKey="is_standalone" />
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff' }}>
                    First TD Team
                  </th>
                  <th onClick={() => handleSort('player')} style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                    First TD Scorer<SortIcon columnKey="player" />
                  </th>
                  <th onClick={() => handleSort('position')} style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #ddd', fontWeight: 600, color: '#fff', cursor: 'pointer', userSelect: 'none' }}>
                    Position<SortIcon columnKey="position" />
                  </th>
                </tr>
              </thead>
              <tbody>
                {historyData.results
                  .filter((r: any) =>
                    (historySeason === 'all' || r.season === parseInt(historySeason)) &&
                    (historyWeek === 'all' || r.week === parseInt(historyWeek)) &&
                    (historyTeam === 'all' || r.team === historyTeam || r.opponent === historyTeam)
                  )
                  .map((r: any, idx: number) => {
                    const homeTeam = r.is_home ? r.team : r.opponent;
                    const awayTeam = r.is_home ? r.opponent : r.team;
                    const gameType = r.is_standalone ? 'Standalone' : 'Mainslate';
                    
                    return (
                      <tr key={idx} style={{ background: idx % 2 === 0 ? '#fff' : '#f8f9fa' }}>
                        <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center', color: '#333' }}>{r.week}</td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{homeTeam}</td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{awayTeam}</td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center' }}>
                          <span style={{
                            ...badgeStyles.mainslate,
                            backgroundColor: r.is_standalone ? colors.warning : colors.info
                          }}>
                            {gameType}
                          </span>
                        </td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{r.team}</td>
                        <td style={{ padding: '10px', border: '1px solid #ddd', color: '#333' }}>{r.player}</td>
                        <td style={{ 
                          padding: '10px', 
                          border: '1px solid #ddd', 
                          color: '#fff',
                          backgroundColor: getPositionColor(r.position),
                          fontWeight: 600,
                          textAlign: 'center'
                        }}>{r.position}</td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          )}
        </>
      )}

      {/* Player Details Modal */}
      {selectedPlayer && (
        <div
          style={modalStyles.overlay}
          onClick={() => setSelectedPlayer(null)}
        >
          <div
            className={styles.modalContainer}
            style={modalStyles.container}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={modalStyles.header}>
              <h2 style={modalStyles.headerTitle}>Player First TD Games</h2>
              <button
                onClick={() => setSelectedPlayer(null)}
                style={modalStyles.closeButton}
              >
                ×
              </button>
            </div>

            {/* Player Info */}
            <div style={modalStyles.body}>
              <h3 style={{ margin: `0 0 ${spacing.md} 0`, fontSize: fontSize.xxl, color: `${colors.textPrimary} !important`, fontWeight: fontWeight.medium }}>{selectedPlayer.name}</h3>
              <div style={{ display: 'flex', gap: spacing.sm, marginBottom: spacing.xxl, alignItems: 'center' }}>
                <span
                  style={{
                    ...badgeStyles.position,
                    backgroundColor: getPositionColor(selectedPlayer.position),
                  }}
                >
                  {selectedPlayer.position}
                </span>
                <span style={{ color: colors.textSecondary, fontSize: fontSize.md }}>{selectedPlayer.team}</span>
              </div>

              {/* First TD Games This Season */}
              <h4 style={{ margin: `0 0 ${spacing.lg} 0`, fontSize: fontSize.md, color: `${colors.textSecondary} !important`, fontWeight: fontWeight.medium }}>
                First TD Games This Season ({selectedPlayer.stats_full?.first_tds || 0})
              </h4>

              {/* Games Table */}
              {historyData && historyData.results && (
                <div style={{ overflowX: 'auto' }}>
                  <table style={tableStyles.table}>
                    <thead style={tableStyles.thead}>
                      <tr>
                        <th style={tableStyles.th}>Week</th>
                        <th style={tableStyles.th}>Opponent</th>
                        <th style={tableStyles.thCenter}>Location</th>
                        <th style={tableStyles.thCenter}>Date</th>
                        <th style={tableStyles.thCenter}>Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historyData.results
                        .filter((game: any) => 
                          game.player === selectedPlayer.name && 
                          game.season === 2025
                        )
                        .map((game: any, idx: number) => {
                          const location = game.is_home ? 'Home' : 'Away';
                          const opponent = game.opponent || '-';
                          const gameDate = game.game_date ? new Date(game.game_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '-';
                          const gameType = game.is_standalone ? 'Standalone' : 'Mainslate';
                          
                          return (
                            <tr key={idx} style={tableStyles.tr}>
                              <td style={tableStyles.td}>{game.week}</td>
                              <td style={tableStyles.td}>{opponent}</td>
                              <td style={tableStyles.tdCenter}>{location}</td>
                              <td style={tableStyles.tdCenter}>{gameDate}</td>
                              <td style={tableStyles.tdCenter}>
                                <span style={{
                                  ...badgeStyles.mainslate,
                                  backgroundColor: game.is_standalone ? colors.warning : colors.info
                                }}>
                                  {gameType}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Summary Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.lg, marginTop: spacing.xxl }}>
                <div style={cardStyles.container}>
                  <div style={cardStyles.label}>Standalone Games</div>
                  <div style={cardStyles.value}>
                    {historyData?.results?.filter((g: any) => g.player === selectedPlayer.name && g.season === 2025 && g.is_standalone).length || 0}
                  </div>
                </div>
                <div style={cardStyles.container}>
                  <div style={cardStyles.label}>Mainslate Games</div>
                  <div style={cardStyles.value}>
                    {historyData?.results?.filter((g: any) => g.player === selectedPlayer.name && g.season === 2025 && !g.is_standalone).length || 0}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Defense Details Modal */}
      {selectedDefense && (
        <div
          style={modalStyles.overlay}
          onClick={() => setSelectedDefense(null)}
        >
          <div
            className={styles.modalContainer}
            style={modalStyles.container}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={modalStyles.header}>
              <h2 style={modalStyles.headerTitle}>Defense vs Position Stats</h2>
              <button
                onClick={() => setSelectedDefense(null)}
                style={modalStyles.closeButton}
              >
                ×
              </button>
            </div>

            {/* Defense Info */}
            <div style={modalStyles.body}>
              <h3 style={{ margin: `0 0 ${spacing.md} 0`, fontSize: fontSize.xxl, color: `${colors.textPrimary} !important`, fontWeight: fontWeight.medium }}>
                {selectedDefense.defense}
              </h3>
              <div style={{ marginBottom: spacing.xxl }}>
                <span style={{ color: colors.textSecondary, fontSize: fontSize.md }}>
                  Funnel Type: <strong>{selectedDefense.funnel_type}</strong>
                </span>
              </div>

              {/* First TDs Allowed by Position */}
              <h4 style={{ margin: `0 0 ${spacing.lg} 0`, fontSize: fontSize.md, color: `${colors.textSecondary} !important`, fontWeight: fontWeight.medium }}>
                First Touchdowns Allowed by Position
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: spacing.lg, marginBottom: spacing.xxl }}>
                <div style={cardStyles.container}>
                  <div style={cardStyles.label}>QB</div>
                  <div style={cardStyles.value}>
                    {selectedDefense.ftds_allowed?.QB || 0}
                  </div>
                  <div style={{ fontSize: fontSize.sm, color: colors.textSecondary, marginTop: spacing.sm }}>
                    Rank: {selectedDefense.qb_rank}
                  </div>
                </div>
                <div style={cardStyles.container}>
                  <div style={cardStyles.label}>RB</div>
                  <div style={cardStyles.value}>
                    {selectedDefense.ftds_allowed?.RB || 0}
                  </div>
                  <div style={{ fontSize: fontSize.sm, color: colors.textSecondary, marginTop: spacing.sm }}>
                    Rank: {selectedDefense.rb_rank}
                  </div>
                </div>
                <div style={cardStyles.container}>
                  <div style={cardStyles.label}>WR</div>
                  <div style={cardStyles.value}>
                    {selectedDefense.ftds_allowed?.WR || 0}
                  </div>
                  <div style={{ fontSize: fontSize.sm, color: colors.textSecondary, marginTop: spacing.sm }}>
                    Rank: {selectedDefense.wr_rank}
                  </div>
                </div>
                <div style={cardStyles.container}>
                  <div style={cardStyles.label}>TE</div>
                  <div style={cardStyles.value}>
                    {selectedDefense.ftds_allowed?.TE || 0}
                  </div>
                  <div style={{ fontSize: fontSize.sm, color: colors.textSecondary, marginTop: spacing.sm }}>
                    Rank: {selectedDefense.te_rank}
                  </div>
                </div>
                <div style={cardStyles.container}>
                  <div style={cardStyles.label}>Other</div>
                  <div style={cardStyles.value}>
                    {selectedDefense.ftds_allowed?.Other || 0}
                  </div>
                </div>
              </div>

              {/* Total Summary */}
              <div style={{ 
                padding: spacing.lg, 
                background: colors.bgLight, 
                borderRadius: borderRadius.sm,
                marginTop: spacing.xl 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: fontSize.lg, color: colors.textPrimary, fontWeight: fontWeight.medium }}>
                    Total First TDs Allowed:
                  </span>
                  <span style={{ fontSize: fontSize.xxl, color: colors.textPrimary, fontWeight: fontWeight.bold }}>
                    {selectedDefense.ftds_allowed?.Total || 0}
                  </span>
                </div>
              </div>

              <div style={{ marginTop: spacing.lg, fontSize: fontSize.sm, color: colors.textSecondary, fontStyle: 'italic' }}>
                * Lower ranks (1-10) indicate more TDs allowed to that position (vulnerable). Higher ranks (22-32) indicate fewer TDs allowed (strong defense).
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analysis;

