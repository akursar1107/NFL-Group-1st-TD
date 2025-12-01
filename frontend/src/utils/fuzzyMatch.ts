// Simple fuzzy string matching utility (Levenshtein distance)

export function levenshtein(a: string, b: string): number {
  const matrix = Array(a.length + 1).fill(null).map(() => Array(b.length + 1).fill(null));
  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost
      );
    }
  }
  return matrix[a.length][b.length];
}

export function fuzzyMatch(a: string, b: string): number {
  const maxLen = Math.max(a.length, b.length);
  if (maxLen === 0) return 1;
  const distance = levenshtein(a.toLowerCase(), b.toLowerCase());
  return 1 - distance / maxLen;
}

export function bestFuzzyMatch(target: string, candidates: string[]): { matched: string, score: number } {
  let bestScore = -1;
  let bestMatch = '';
  for (const candidate of candidates) {
    const score = fuzzyMatch(target, candidate);
    if (score > bestScore) {
      bestScore = score;
      bestMatch = candidate;
    }
  }
  return { matched: bestMatch, score: bestScore };
}
