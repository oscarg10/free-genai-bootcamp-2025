import { useState, useEffect } from 'react';
import './Game.css';
import { Card } from './Card';
import { Card as CardType, Difficulty, GameState, Category, WordPair } from '../types';
import { wordSets } from '../data/wordSets';
import { LearningAssistant } from './LearningAssistant';

const createCards = (difficulty: Difficulty, category: Category = 'general'): CardType[] => {
  const selectedWords = wordSets[category].words
    .filter(word => word.difficulty === difficulty)
    .map(word => ({ german: word.german, english: word.english }));
  const shuffledWords = [...selectedWords].sort(() => Math.random() - 0.5);
  const cards: CardType[] = [];

  shuffledWords.forEach((pair, index) => {
    cards.push(
      {
        id: index * 2,
        word: pair.german,
        translation: pair.english,
        isFlipped: false,
        isMatched: false,
        language: 'german'
      },
      {
        id: index * 2 + 1,
        word: pair.english,
        translation: pair.german,
        isFlipped: false,
        isMatched: false,
        language: 'english'
      }
    );
  });

  return cards.sort(() => Math.random() - 0.5);
};

export const Game = () => {
  const [selectedCategory, setSelectedCategory] = useState<Category>('general');
  const [currentWord, setCurrentWord] = useState<WordPair | undefined>();
  
  const [gameState, setGameState] = useState<GameState>({
    cards: [],
    flippedCards: [],
    score: 0,
    tries: 0,
    difficulty: 'easy',
    gameStarted: false
  });

  const startGame = () => {
    setGameState(prev => ({
      ...prev,
      cards: createCards(prev.difficulty, selectedCategory),
      flippedCards: [],
      score: 0,
      tries: 0,
      gameStarted: true
    }));
  };

  const handleCardClick = (card: CardType) => {
    // Update current word for Learning Assistant
    const wordPair = wordSets[selectedCategory].words.find(
      w => w.german === card.word || w.english === card.word
    );
    if (wordPair) {
      setCurrentWord(wordPair);
    }
    if (card.isMatched || card.isFlipped || gameState.flippedCards.length >= 2) return;

    const newCards = gameState.cards.map(c =>
      c.id === card.id ? { ...c, isFlipped: true } : c
    );

    const newFlippedCards = [...gameState.flippedCards, card];

    setGameState(prev => ({
      ...prev,
      cards: newCards,
      flippedCards: newFlippedCards
    }));
  };

  useEffect(() => {
    if (gameState.flippedCards.length === 2) {
      const [first, second] = gameState.flippedCards;
      const isMatch = first.word === second.translation || second.word === first.translation;

      setTimeout(() => {
        const newCards = gameState.cards.map(card =>
          card.id === first.id || card.id === second.id
            ? { ...card, isFlipped: false, isMatched: isMatch }
            : card
        );

        setGameState(prev => ({
          ...prev,
          cards: newCards,
          flippedCards: [],
          score: isMatch ? prev.score + 1 : prev.score,
          tries: prev.tries + 1
        }));
      }, 1000);
    }
  }, [gameState.flippedCards]);

  const handleDifficultyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setGameState(prev => ({
      ...prev,
      difficulty: e.target.value as Difficulty,
      gameStarted: false
    }));
  };

  const isGameComplete = gameState.gameStarted && 
    gameState.cards.every(card => card.isMatched);

  return (
    <div className="game">
      <h1 className="game-title">
        German-English Memory Game
      </h1>
      
      <div className="game-controls">
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value as Category)}
          className="category-select"
        >
          <option value="general">General</option>
          <option value="cooking">Cooking</option>
          <option value="travel">Travel</option>
          <option value="business">Business</option>
          <option value="technology">Technology</option>
        </select>
        <select
          value={gameState.difficulty}
          onChange={handleDifficultyChange}
        >
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <button onClick={startGame}>
          {gameState.gameStarted ? 'Restart Game' : 'Start Game'}
        </button>
      </div>

      {gameState.gameStarted && (
        <div className="game-board">
          <div className="stats">
            <div className="score">Score: {gameState.score}</div>
            <div className="tries">Tries: {gameState.tries}</div>
          </div>
          <div className={`card-grid difficulty-${gameState.difficulty}`}>
            {gameState.cards.map(card => (
              <Card
                key={card.id}
                card={card}
                onClick={() => handleCardClick(card)}
              />
            ))}
          </div>
        </div>
      )}
      <LearningAssistant currentCard={currentWord} />

      {isGameComplete && (
        <div className="game-complete">
          <h2>Congratulations!</h2>
          <p>You've completed the game with a score of {gameState.score}!</p>
          <p>Total tries: {gameState.tries}</p>
        </div>
      )}
    </div>

  );
};
