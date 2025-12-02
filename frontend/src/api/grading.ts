const API_BASE_URL = 'http://localhost:5000/api';

export interface GradeWeekResponse {
  message: string;
  graded_count: number;
  week: number;
  season: number;
}

export interface GradeByTypeResponse {
  message: string;
  season: number;
  pick_type: string;
  weeks_graded: number;
  total_graded: number;
  total_won: number;
  total_lost: number;
  total_needs_review: number;
}

export const gradeWeek = async (week: number, season: number = 2025): Promise<GradeWeekResponse> => {
  const response = await fetch(`${API_BASE_URL}/grade-week`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ week, season }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to grade week');
  }

  return response.json();
};

export const gradeByType = async (pickType: 'FTD' | 'ATTS', season: number = 2025): Promise<GradeByTypeResponse> => {
  const response = await fetch(`${API_BASE_URL}/grade-by-type`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ pick_type: pickType, season }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to grade picks by type');
  }

  return response.json();
};
