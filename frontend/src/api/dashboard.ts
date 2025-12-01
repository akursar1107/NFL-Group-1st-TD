export interface RecentPick {
  id: number;
  user_name: string;
  week: number;
  game: string;
  pick_type: 'FTD' | 'ATTS';
  player_name: string;
  result: 'W' | 'L' | 'Pending' | 'Push';
  payout: number;
}

export interface DashboardStats {
  total_players: number;
  current_week: number;
  total_picks_this_week: number;
  pending_picks: number;
  league_ftd_bankroll: number;
  league_atts_bankroll: number;
  overall_win_rate: number;
  games_this_week: number;
  games_graded: number;
  recent_picks: RecentPick[];
}

export async function fetchDashboardStats(season: number): Promise<DashboardStats> {
  const response = await fetch(`http://localhost:5000/api/admin/dashboard-stats?season=${season}`);
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || 'Failed to fetch dashboard stats');
  }
  return response.json();
}
