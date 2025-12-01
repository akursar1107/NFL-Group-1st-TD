import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchPicks, Pick, deletePick } from '../api/picks';
import { fetchUsers, User } from '../api/picks';
import '../styles/AllPicks.css';

const AllPicks: React.FC = () => {
  const navigate = useNavigate();
  const [allPicks, setAllPicks] = useState<Pick[]>([]);
  const [filteredPicks, setFilteredPicks] = useState<Pick[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [selectedUser, setSelectedUser] = useState<string>('all');
  const [selectedWeek, setSelectedWeek] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [season, setSeason] = useState(2025);

  // Sort state
  const [sortBy, setSortBy] = useState<'week' | 'user' | 'result'>('week');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    loadData();
  }, [season]);

  useEffect(() => {
    applyFilters();
  }, [allPicks, selectedUser, selectedWeek, selectedStatus, selectedType, sortBy, sortOrder]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [picksResponse, usersResponse] = await Promise.all([
        fetchPicks(season),
        fetchUsers()
      ]);
      setAllPicks(picksResponse.picks);
      setUsers(usersResponse.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load picks');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...allPicks];

    // User filter
    if (selectedUser !== 'all') {
      filtered = filtered.filter(p => p.user_id === parseInt(selectedUser));
    }

    // Week filter
    if (selectedWeek !== 'all') {
      filtered = filtered.filter(p => p.week === parseInt(selectedWeek));
    }

    // Status filter
    if (selectedStatus !== 'all') {
      filtered = filtered.filter(p => p.result === selectedStatus);
    }

    // Type filter
    if (selectedType !== 'all') {
      filtered = filtered.filter(p => p.pick_type === selectedType);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'week':
          comparison = a.week - b.week;
          break;
        case 'user':
          comparison = a.username.localeCompare(b.username);
          break;
        case 'result':
          comparison = a.result.localeCompare(b.result);
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredPicks(filtered);
  };

  const getAvailableWeeks = () => {
    const weeks = Array.from(new Set(allPicks.map(p => p.week))).sort((a, b) => a - b);
    return weeks;
  };

  const getResultBadge = (result: string) => {
    const classMap: { [key: string]: string } = {
      W: 'result-win',
      L: 'result-loss',
      Pending: 'result-pending',
      Push: 'result-push',
    };
    return <span className={`result-badge ${classMap[result] || ''}`}>{result}</span>;
  };

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : odds.toString();
  };

  const formatPayout = (payout: number) => {
    const sign = payout >= 0 ? '+' : '';
    return `${sign}$${payout.toFixed(2)}`;
  };

  const getBankrollColor = (amount: number) => {
    if (amount > 0) return 'payout-positive';
    if (amount < 0) return 'payout-negative';
    return 'payout-neutral';
  };

  const handleSort = (column: 'week' | 'user' | 'result') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const handleDeletePick = async (pickId: number, playerName: string) => {
    const confirmMessage = `Are you sure you want to delete the pick for ${playerName}? This action cannot be undone.`;
    if (!window.confirm(confirmMessage)) return;

    try {
      await deletePick(pickId);
      // Reload picks after deletion
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete pick');
    }
  };

  // Calculate stats
  const stats = {
    total: filteredPicks.length,
    wins: filteredPicks.filter(p => p.result === 'W').length,
    losses: filteredPicks.filter(p => p.result === 'L').length,
    pending: filteredPicks.filter(p => p.result === 'Pending').length,
    totalPayout: filteredPicks.reduce((sum, p) => sum + p.payout, 0),
    ftdCount: filteredPicks.filter(p => p.pick_type === 'FTD').length,
    attsCount: filteredPicks.filter(p => p.pick_type === 'ATTS').length,
  };

  if (loading) {
    return (
      <div className="all-picks-container">
        <div className="loading">Loading all picks...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="all-picks-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="all-picks-container">
      <div className="all-picks-header">
        <h1>All Picks</h1>
        <div className="season-selector">
          <label htmlFor="season">Season:</label>
          <select
            id="season"
            value={season}
            onChange={(e) => setSeason(parseInt(e.target.value))}
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
          </select>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="stats-summary">
        <div className="stat-card">
          <div className="stat-label">Total Picks</div>
          <div className="stat-value">{stats.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Wins</div>
          <div className="stat-value stat-wins">{stats.wins}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Losses</div>
          <div className="stat-value stat-losses">{stats.losses}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending</div>
          <div className="stat-value stat-pending">{stats.pending}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Payout</div>
          <div className={`stat-value ${getBankrollColor(stats.totalPayout)}`}>
            {formatPayout(stats.totalPayout)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">FTD / ATTS</div>
          <div className="stat-value">{stats.ftdCount} / {stats.attsCount}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="userFilter">User:</label>
          <select
            id="userFilter"
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
          >
            <option value="all">All Users</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.display_name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="weekFilter">Week:</label>
          <select
            id="weekFilter"
            value={selectedWeek}
            onChange={(e) => setSelectedWeek(e.target.value)}
          >
            <option value="all">All Weeks</option>
            {getAvailableWeeks().map(week => (
              <option key={week} value={week}>
                Week {week}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="statusFilter">Status:</label>
          <select
            id="statusFilter"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="W">Win</option>
            <option value="L">Loss</option>
            <option value="Pending">Pending</option>
            <option value="Push">Push</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="typeFilter">Type:</label>
          <select
            id="typeFilter"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="FTD">First TD</option>
            <option value="ATTS">Anytime TD</option>
          </select>
        </div>

        <button 
          className="btn-reset"
          onClick={() => {
            setSelectedUser('all');
            setSelectedWeek('all');
            setSelectedStatus('all');
            setSelectedType('all');
          }}
        >
          Reset Filters
        </button>
      </div>

      {/* Picks Table */}
      <div className="table-container">
        <table className="picks-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('week')} className="sortable">
                Week {sortBy === 'week' && (sortOrder === 'asc' ? '▲' : '▼')}
              </th>
              <th onClick={() => handleSort('user')} className="sortable">
                User {sortBy === 'user' && (sortOrder === 'asc' ? '▲' : '▼')}
              </th>
              <th>Game</th>
              <th>Type</th>
              <th>Player</th>
              <th>Pos</th>
              <th>Odds</th>
              <th>Stake</th>
              <th onClick={() => handleSort('result')} className="sortable">
                Result {sortBy === 'result' && (sortOrder === 'asc' ? '▲' : '▼')}
              </th>
              <th>Payout</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredPicks.length === 0 ? (
              <tr>
                <td colSpan={11} className="no-picks">
                  No picks found matching the selected filters
                </td>
              </tr>
            ) : (
              filteredPicks.map(pick => (
                <tr key={pick.id}>
                  <td>{pick.week}</td>
                  <td>{pick.username}</td>
                  <td className="game-cell">{pick.game_matchup}</td>
                  <td>
                    <span className={`pick-type-badge ${pick.pick_type.toLowerCase()}`}>
                      {pick.pick_type}
                    </span>
                  </td>
                  <td className="player-cell">{pick.player_name}</td>
                  <td>{pick.player_position}</td>
                  <td className="odds-cell">{formatOdds(pick.odds)}</td>
                  <td>${pick.stake.toFixed(2)}</td>
                  <td>{getResultBadge(pick.result)}</td>
                  <td className={getBankrollColor(pick.payout)}>
                    {formatPayout(pick.payout)}
                  </td>
                  <td>
                    <div className="action-buttons-cell">
                      <button
                        onClick={() => navigate(`/edit-pick/${pick.id}`)}
                        className="btn-edit-small"
                        title="Edit pick"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeletePick(pick.id, pick.player_name)}
                        className="btn-delete-small"
                        title="Delete pick"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AllPicks;
