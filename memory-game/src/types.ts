export interface Card {
  id: number;
  word: string;
  translation: string;
  isFlipped: boolean;
  isMatched: boolean;
  language: 'german' | 'english';
}

export type Difficulty = 'easy' | 'medium' | 'hard';

export type Category = 'general' | 'cooking' | 'travel' | 'business' | 'technology';

export interface WordPair {
    german: string;
    english: string;
    examples: string[];
    category: Category;
    difficulty: Difficulty;
}

export interface WordSet {
    category: Category;
    words: WordPair[];
}

export interface ChatMessage {
    text: string;
    type: 'user' | 'bot';
    timestamp: number;
}

export interface GameState {
  cards: Card[];
  flippedCards: Card[];
  score: number;
  tries: number;
  difficulty: Difficulty;
  gameStarted: boolean;
  isLoading: boolean;
  generatedWords: WordPair[];
}
