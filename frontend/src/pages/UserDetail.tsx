import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchUserDetail, UserDetailResponse, UserPick, WeeklyStats } from '../api/userDetail';
import '../styles/UserDetail.css';

const UserDetail: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const [season, setSeason] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userData, setUserData] = useState<UserDetailResponse | null>(null);

  useEffect(() => {
    if (!userId) {
      setError('User ID is required');
      setLoading(false);
      return;
    }

    const loadUserData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchUserDetail(parseInt(userId), season);
        setUserData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load user data');
      } finally {
        setLoading(false);
      }
    };

    loadUserData();
  }, [userId, season]);

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

  const formatCurrency = (amount: number) => {
    const sign = amount >= 0 ? '+' : '';
    return `${sign}$${amount.toFixed(2)}`;
  };

  const getBankrollColor = (amount: number) => {
    if (amount > 0) return 'bankroll-positive';
    if (amount < 0) return 'bankroll-negative';
    return 'bankroll-neutral';
  };

  if (loading) {
    return (
      <div className="user-detail-container">
        <div className="loading">Loading user details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-detail-container">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/standings')} className="btn-back">
          ← Back to Standings
        </button>
      </div>
    );
  }

  if (!userData) {
    return (
      <div className="user-detail-container">
        <div className="error-message">No user data available</div>
      </div>
    );
  }

  const { user, stats, weekly_stats, picks } = userData;

  return (
    <div className="user-detail-container">
      <div className="user-detail-header">
        <button onClick={() => navigate('/standings')} className="btn-back">
          ← Back
        </button>
        <h1>{user.display_name}'s Performance</h1>
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

      {/* Overall Stats Cards */}
      <div className="stats-cards">
        <div className="stats-card">
          <h3>First TD</h3>
          <div className="stat-row">
            <span className="stat-label">Record:</span>
            <span className="stat-value">
              {stats.ftd.wins}-{stats.ftd.losses}-{stats.ftd.pending}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Win Rate:</span>
            <span className="stat-value">{stats.ftd.win_rate}%</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Bankroll:</span>
            <span className={`stat-value ${getBankrollColor(stats.ftd.bankroll)}`}>
              {formatCurrency(stats.ftd.bankroll)}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Picks:</span>
            <span className="stat-value">{stats.ftd.total_picks}</span>
          </div>
        </div>

        <div className="stats-card">
          <h3>Anytime TD</h3>
          <div className="stat-row">
            <span className="stat-label">Record:</span>
            <span className="stat-value">
              {stats.atts.wins}-{stats.atts.losses}-{stats.atts.pending}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Win Rate:</span>
            <span className="stat-value">{stats.atts.win_rate}%</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Bankroll:</span>
            <span className={`stat-value ${getBankrollColor(stats.atts.bankroll)}`}>
              {formatCurrency(stats.atts.bankroll)}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Picks:</span>
            <span className="stat-value">{stats.atts.total_picks}</span>
          </div>
        </div>

        <div className="stats-card stats-card-total">
          <h3>Combined Total</h3>
          <div className="stat-row">
            <span className="stat-label">Record:</span>
            <span className="stat-value">
              {stats.total.wins}-{stats.total.losses}-{stats.total.pending}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Bankroll:</span>
            <span className={`stat-value stat-value-large ${getBankrollColor(stats.total.bankroll)}`}>
              {formatCurrency(stats.total.bankroll)}
            </span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Picks:</span>
            <span className="stat-value">{stats.total.picks}</span>
          </div>
        </div>
      </div>

      {/* Weekly Breakdown */}
      {weekly_stats.length > 0 && (
        <div className="weekly-breakdown">
          <h2>Weekly Performance</h2>
          <div className="table-container">
            <table className="weekly-table">
              <thead>
                <tr>
                  <th>Week</th>
                  <th>FTD Record</th>
                  <th>FTD $</th>
                  <th>ATTS Record</th>
                  <th>ATTS $</th>
                  <th>Total Picks</th>
                  <th>Weekly Total</th>
                </tr>
              </thead>
              <tbody>
                {weekly_stats.map((week: WeeklyStats) => {
                  const weeklyTotal = week.ftd_bankroll + week.atts_bankroll;
                  return (
                    <tr key={week.week}>
                      <td className="week-cell">Week {week.week}</td>
                      <td>
                        {week.ftd_wins}-{week.ftd_losses}-{week.ftd_pending}
                      </td>
                      <td className={getBankrollColor(week.ftd_bankroll)}>
                        {formatCurrency(week.ftd_bankroll)}
                      </td>
                      <td>
                        {week.atts_wins}-{week.atts_losses}-{week.atts_pending}
                      </td>
                      <td className={getBankrollColor(week.atts_bankroll)}>
                        {formatCurrency(week.atts_bankroll)}
                      </td>
                      <td>{week.total_picks}</td>
                      <td className={getBankrollColor(weeklyTotal)}>
                        <strong>{formatCurrency(weeklyTotal)}</strong>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* All Picks History */}
      {picks.length > 0 && (
        <div className="picks-history">
          <h2>Complete Pick History ({picks.length} picks)</h2>
          <div className="table-container">
            <table className="picks-table">
              <thead>
                <tr>
                  <th>Week</th>
                  <th>Game</th>
                  <th>Type</th>
                  <th>Player</th>
                  <th>Pos</th>
                  <th>Odds</th>
                  <th>Stake</th>
                  <th>Result</th>
                  <th>Payout</th>
                </tr>
              </thead>
              <tbody>
                {picks.map((pick: UserPick) => (
                  <tr key={pick.id} className={pick.is_final ? '' : 'pending-game'}>
                    <td>{pick.week}</td>
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
                      {formatCurrency(pick.payout)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {picks.length === 0 && (
        <div className="no-picks-message">
          <p>No picks found for {user.display_name} in the {season} season.</p>
        </div>
      )}
    </div>
  );
};

export default UserDetail;
