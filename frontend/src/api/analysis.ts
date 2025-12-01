// src/api/analysis.ts
export async function fetchAnalysis(season: number = 2025) {
  const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/api/analysis?season=${season}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
