export interface Card {
  id: number;
  word: string;
  translation: string;
  isFlipped: boolean;
  isMatched: boolean;
  language: 'german' | 'english';
}

export type Difficulty = 'easy' | 'medium' | 'hard';

export interface GameState {
  cards: Card[];
  flippedCards: Card[];
  score: number;
  difficulty: Difficulty;
  gameStarted: boolean;
}
