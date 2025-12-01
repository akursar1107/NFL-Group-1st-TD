const API_BASE_URL = 'http://localhost:5000/api';

export interface GradeWeekResponse {
  message: string;
  graded_count: number;
  week: number;
  season: number;
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
