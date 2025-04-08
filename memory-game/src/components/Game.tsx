import { useState, useEffect } from 'react';
import './Game.css';
import { Card } from './Card';
import { Card as CardType, Difficulty, GameState } from '../types';
import { words } from '../data/words';

const createCards = (difficulty: Difficulty): CardType[] => {
  const selectedWords = words[difficulty];
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
  const [gameState, setGameState] = useState<GameState>({
    cards: [],
    flippedCards: [],
    score: 0,
    difficulty: 'easy',
    gameStarted: false
  });

  const startGame = () => {
    setGameState(prev => ({
      ...prev,
      cards: createCards(prev.difficulty),
      flippedCards: [],
      score: 0,
      gameStarted: true
    }));
  };

  const handleCardClick = (card: CardType) => {
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
          score: isMatch ? prev.score + 1 : prev.score
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
          <div className="score">Score: {gameState.score}</div>
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

      {isGameComplete && (
        <div className="game-complete">
          <h2>Congratulations!</h2>
          <p>You've completed the game with a score of {gameState.score}!</p>
        </div>
      )}
    </div>

  );
};
