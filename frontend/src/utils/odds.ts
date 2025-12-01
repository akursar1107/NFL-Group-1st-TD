// Utility functions for odds conversion and calculations

export function americanToDecimal(americanOdds: number): number {
  if (americanOdds > 0) {
    return (americanOdds / 100) + 1;
  } else {
    return (100 / Math.abs(americanOdds)) + 1;
  }
}

export function decimalToAmerican(decimalOdds: number): number {
  if (decimalOdds >= 2) {
    return Math.round((decimalOdds - 1) * 100);
  } else {
    return Math.round(-100 / (decimalOdds - 1));
  }
}

export function impliedProbability(decimalOdds: number): number {
  return 1 / decimalOdds;
}

export function calculateFairOdds(playerProb: number, defenseAdjustment: number = 0, rzBoost: number = 1, odBoost: number = 1) {
  // Adjust probability
  const adjustedProb = playerProb * defenseAdjustment * rzBoost * odBoost;
  const decimal = adjustedProb > 0 ? 1 / adjustedProb : 0;
  const american = decimalToAmerican(decimal);
  return {
    american,
    decimal,
    impliedProb: adjustedProb
  };
}

export function calculateKellyCriterion(fairOddsDecimal: number, marketOddsDecimal: number, kellyFraction: number = 0.25) {
  const b = marketOddsDecimal - 1;
  const p = impliedProbability(fairOddsDecimal);
  const q = 1 - p;
  const f = (b * p - q) / b;
  return {
    kellyPct: Math.max(0, f * kellyFraction),
    expectedValue: (marketOddsDecimal * p) - 1,
    evPct: ((marketOddsDecimal * p) - 1) * 100,
    edge: (marketOddsDecimal * p) - fairOddsDecimal
  };
}
