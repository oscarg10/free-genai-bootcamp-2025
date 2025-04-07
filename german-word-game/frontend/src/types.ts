export type Difficulty = 'easy' | 'medium' | 'hard';

export interface Card {
  id: number;
  word: string;
  translation: string;
  isFlipped: boolean;
  isMatched: boolean;
}

export interface MatchedWord {
  german: string;
  english: string;
}

export interface Progress {
  matchedWords: MatchedWord[];
  totalMatches: number;
  needsReview: string[];
  mastered: string[];
  suggestions: string[];
}

export interface GameState {
  score: number;
  moves: number;
  cards: Card[];
  firstCard: Card | null;
  secondCard: Card | null;
  difficulty: Difficulty;
  showLearningPanel: boolean;
  matchedWords: MatchedWord[];
  progress: Progress | null;
}
