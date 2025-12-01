const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface PickData {
  id: number;
  user_id: number;
  username: string;
  player_name: string;
  player_position: string;
  odds: number;
  stake: number;
  result: string; // 'W', 'L', 'Pending', 'Push'
  payout: number;
  graded_at: string | null;
}

export interface GameDetailData {
  game_id: string;
  db_id: number;
  week: number;
  matchup: string;
  home_team: string;
  away_team: string;
  game_date: string | null;
  game_time: string | null;
  is_final: boolean;
  home_score: number | null;
  away_score: number | null;
  actual_first_td_player: string | null;
  ftd_picks: PickData[];
  atts_picks: PickData[];
  total_picks: number;
}

export interface WeekDetailResponse {
  games: GameDetailData[];
  week: number;
  season: number;
  available_weeks: number[];
  message?: string;
  error?: string;
}

export const fetchWeekDetail = async (season: number = 2025, week: number): Promise<WeekDetailResponse> => {
  const url = `${API_BASE_URL}/api/week-detail?season=${season}&week=${week}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch week detail');
  }
  return response.json();
};
