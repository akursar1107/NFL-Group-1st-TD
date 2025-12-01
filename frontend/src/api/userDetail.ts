const API_BASE_URL = 'http://localhost:5000/api';

export interface UserInfo {
  id: number;
  username: string;
  display_name: string;
}

export interface PickTypeStats {
  wins: number;
  losses: number;
  pending: number;
  bankroll: number;
  total_picks: number;
  win_rate: number;
}

export interface TotalStats {
  picks: number;
  wins: number;
  losses: number;
  pending: number;
  bankroll: number;
}

export interface UserStats {
  ftd: PickTypeStats;
  atts: PickTypeStats;
  total: TotalStats;
}

export interface WeeklyStats {
  week: number;
  ftd_wins: number;
  ftd_losses: number;
  ftd_pending: number;
  ftd_bankroll: number;
  atts_wins: number;
  atts_losses: number;
  atts_pending: number;
  atts_bankroll: number;
  total_picks: number;
}

export interface UserPick {
  id: number;
  week: number;
  game_matchup: string;
  game_date: string | null;
  pick_type: 'FTD' | 'ATTS';
  player_name: string;
  player_position: string;
  odds: number;
  stake: number;
  result: 'W' | 'L' | 'Pending' | 'Push';
  payout: number;
  graded_at: string | null;
  is_final: boolean;
}

export interface UserDetailResponse {
  user: UserInfo;
  season: number;
  stats: UserStats;
  weekly_stats: WeeklyStats[];
  picks: UserPick[];
}

export async function fetchUserDetail(userId: number, season: number = 2025): Promise<UserDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/user/${userId}?season=${season}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to fetch user details');
  }
  
  return response.json();
}
