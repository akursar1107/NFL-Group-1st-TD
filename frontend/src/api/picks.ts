const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export interface Pick {
  id: number;
  user_id: number;
  username: string;
  game_id: number;
  game_matchup: string;
  week: number;
  pick_type: string;
  player_name: string;
  player_position: string;
  odds: number;
  stake: number;
  result: string;
  payout: number;
  graded_at: string | null;
}

export interface CreatePickData {
  user_id: number;
  game_id: number;
  pick_type: string;
  player_name: string;
  player_position?: string;
  odds: number;
  stake?: number;
}

export interface UpdatePickData {
  player_name?: string;
  player_position?: string;
  pick_type?: string;
  odds?: number;
  stake?: number;
}

export interface PicksResponse {
  picks: Pick[];
  error?: string;
}

export interface User {
  id: number;
  username: string;
  display_name: string;
}

export interface Game {
  id: number;
  game_id: string;
  week: number;
  season: number;
  matchup: string;
  home_team: string;
  away_team: string;
  game_date: string | null;
  game_time: string | null;
  is_final: boolean;
}

export const fetchPicks = async (season?: number, week?: number, userId?: number): Promise<PicksResponse> => {
  const params = new URLSearchParams();
  if (season) params.append('season', season.toString());
  if (week) params.append('week', week.toString());
  if (userId) params.append('user_id', userId.toString());
  
  const url = `${API_BASE_URL}/api/picks?${params.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch picks');
  }
  return response.json();
};

export const createPick = async (pickData: CreatePickData): Promise<{ message: string; pick_id: number }> => {
  const response = await fetch(`${API_BASE_URL}/api/picks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(pickData),
  });
  
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to create pick');
  }
  return data;
};

export const updatePick = async (pickId: number, pickData: UpdatePickData): Promise<{ message: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/picks/${pickId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(pickData),
  });
  
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to update pick');
  }
  return data;
};

export const deletePick = async (pickId: number): Promise<{ message: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/picks/${pickId}`, {
    method: 'DELETE',
  });
  
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Failed to delete pick');
  }
  return data;
};

export const fetchUsers = async (): Promise<{ users: User[] }> => {
  const response = await fetch(`${API_BASE_URL}/api/users`);
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  return response.json();
};

export const fetchGames = async (season: number = 2025, week?: number): Promise<{ games: Game[] }> => {
  const params = new URLSearchParams({ season: season.toString() });
  if (week) params.append('week', week.toString());
  
  const url = `${API_BASE_URL}/api/games?${params.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch games');
  }
  return response.json();
};
