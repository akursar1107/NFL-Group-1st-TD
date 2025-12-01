const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface StandingData {
  user_id: number;
  username: string;
  display_name: string;
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

export interface StandingsStats {
  total_players: number;
  total_ftd_picks: number;
  total_wins: number;
  win_rate: number;
  league_ftd_bankroll: number;
  league_atts_bankroll: number;
  league_total_bankroll: number;
}

export interface StandingsResponse {
  standings: StandingData[];
  season: number;
  stats: StandingsStats;
}

export const fetchStandings = async (season: number = 2025): Promise<StandingsResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/standings?season=${season}`);
  if (!response.ok) {
    throw new Error('Failed to fetch standings');
  }
  return response.json();
};
