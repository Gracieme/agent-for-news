export interface DimensionEntry {
  cardName: string;
  reversed: boolean;
  numerology: { number: number | null; energy: string; meaning: string };
  color: { dominant: string[]; signals: string };
  astrology: { sign: string; planet: string; influence: string };
  elements: { composition: string; analysis: string };
  symbolism: { symbols: string[]; interpretation: string };
  kabbalah?: { path: string; planets: string; depth: string };
}

export interface TimingReference {
  cardName: string;
  cardNumber: number | null;
  suit: string | null;
  weeksEstimate: number | null;
  zodiacMonth: string | null;
  summary: string;
}
