const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface GameData {
  game_id: string;
  week: number;
  gameday: string;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  game_type: string;
}

export interface TDScorer {
  order: number;
  player: string;
  team: string;
  position?: string;
  quarter?: number;
  time?: string;
  is_first_td: boolean;
}

export interface GameTouchdownsResponse {
  touchdowns: TDScorer[];
  game_id: string;
  error?: string;
}

export interface WeeklyGamesResponse {
  games: GameData[];
  week: number;
  season: number;
  error?: string;
}

export const fetchWeeklyGames = async (season: number = 2025, week?: number): Promise<WeeklyGamesResponse> => {
  const url = week 
    ? `${API_BASE_URL}/api/weekly-games?season=${season}&week=${week}`
    : `${API_BASE_URL}/api/weekly-games?season=${season}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch weekly games');
  }
  return response.json();
};

export const fetchGameTouchdowns = async (gameId: string, season: number = 2025): Promise<GameTouchdownsResponse> => {
  const url = `${API_BASE_URL}/api/game-touchdowns/${gameId}?season=${season}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch game touchdowns');
  }
  return response.json();
};
