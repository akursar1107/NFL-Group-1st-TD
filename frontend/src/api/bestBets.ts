const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface BetData {
  player: string;
  team: string;
  opponent: string;
  position: string;
  prob: number;
  fair_odds: number;
  best_odds: number;
  sportsbook: string;
  ev: number;
  kelly: number;
  first_tds: number;
  games: number;
  rz_opps: number;
  rz_tds: number;
  od_opps: number;
  od_tds: number;
  funnel_type: string | null;
  game_id: string;
}

export interface BestBetsResponse {
  bets: BetData[];
  week: number;
  season: number;
  last_updated: string;
  error?: string;
}

export const fetchBestBets = async (season: number = 2025): Promise<BestBetsResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/best-bets?season=${season}`);
  if (!response.ok) {
    throw new Error('Failed to fetch best bets');
  }
  return response.json();
};
