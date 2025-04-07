import { useState, useEffect } from 'react';
import { Grid, Text, Button, Stack } from '@chakra-ui/react';
import { WordCard } from './WordCard';
import { LearningPanel } from './LearningPanel';
import { Card, GameState, Difficulty } from '../types';

const allWords = [
  { german: 'Hund', english: 'dog' },
  { german: 'Katze', english: 'cat' },
  { german: 'Haus', english: 'house' },
  { german: 'Baum', english: 'tree' },
  { german: 'Buch', english: 'book' },
  { german: 'Auto', english: 'car' },
  { german: 'Apfel', english: 'apple' },
  { german: 'Wasser', english: 'water' },
  { german: 'Brot', english: 'bread' },
  { german: 'Tisch', english: 'table' },
  { german: 'Stuhl', english: 'chair' },
  { german: 'Fenster', english: 'window' },
  { german: 'Sonne', english: 'sun' },
  { german: 'Mond', english: 'moon' },
  { german: 'Stern', english: 'star' },
  { german: 'Blume', english: 'flower' },
  { german: 'Vogel', english: 'bird' },
  { german: 'Fisch', english: 'fish' },
  { german: 'Milch', english: 'milk' },
  { german: 'Kaffee', english: 'coffee' },
];

const PAIRS_BY_DIFFICULTY = {
  easy: 6,
  medium: 8,
  hard: 10,
};

const getRandomWords = (difficulty: Difficulty) => {
  const numPairs = PAIRS_BY_DIFFICULTY[difficulty];
  const shuffled = [...allWords].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, numPairs);
};

const userId = 'user1'; // In a real app, this would come from authentication

export const Game = () => {
  const [gameState, setGameState] = useState<GameState>({
    score: 0,
    moves: 0,
    cards: [],
    firstCard: null,
    secondCard: null,
    difficulty: 'easy',
    showLearningPanel: false,
    matchedWords: [],
    progress: null,
  });

  const initializeGame = (newDifficulty?: Difficulty) => {
    const difficulty = newDifficulty || gameState.difficulty;
    const cards: Card[] = [];
    const selectedWords = getRandomWords(difficulty);
    selectedWords.forEach((word, index) => {
      // Add German word card
      cards.push({
        id: index * 2,
        word: word.german,
        translation: word.english,
        isFlipped: false,
        isMatched: false,
      });
      // Add English word card
      cards.push({
        id: index * 2 + 1,
        word: word.english,
        translation: word.german,
        isFlipped: false,
        isMatched: false,
      });
    });

    // Shuffle cards
    const shuffledCards = cards.sort(() => Math.random() - 0.5);
    setGameState({
      score: 0,
      moves: 0,
      cards: shuffledCards,
      firstCard: null,
      secondCard: null,
      difficulty,
      showLearningPanel: false,
      matchedWords: [],
      progress: null,
    });
  };

  useEffect(() => {
    initializeGame();
  }, []);

  const handleCardClick = (clickedCard: Card) => {
    if (clickedCard.isMatched || clickedCard.isFlipped) return;

    const updatedCards = gameState.cards.map(card =>
      card.id === clickedCard.id ? { ...card, isFlipped: true } : card
    );

    if (!gameState.firstCard) {
      setGameState(prevState => ({
        ...prevState,
        cards: updatedCards,
        firstCard: clickedCard,
      }));
    } else if (!gameState.secondCard) {
      setGameState(prevState => ({
        ...prevState,
        cards: updatedCards,
        secondCard: clickedCard,
        moves: prevState.moves + 1,
      }));

      // Check for match
      if (!gameState.firstCard) return;

      const firstCard = gameState.firstCard; // Store reference to avoid null checks
      const isMatch = (
        firstCard.word === clickedCard.translation ||
        firstCard.translation === clickedCard.word
      );

      setTimeout(async () => {
        const finalCards = updatedCards.map(card =>
          (card.id === firstCard.id || card.id === clickedCard.id)
            ? { ...card, isFlipped: false, isMatched: isMatch }
            : card
        );

        if (isMatch) {
          // Get the matched pair
          const matchedPair = {
            german: firstCard.word,
            english: clickedCard.word,
          };

          try {
            // Update progress on the server
            const response = await fetch('http://localhost:3001/api/progress', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                userId,
                matchedPair,
                difficulty: gameState.difficulty,
              }),
            });

            if (!response.ok) throw new Error('Failed to update progress');

            const { progress } = await response.json();

            setGameState(prevState => ({
              ...prevState,
              cards: finalCards,
              firstCard: null,
              secondCard: null,
              score: prevState.score + 1,
              matchedWords: [...prevState.matchedWords, matchedPair],
              progress,
              showLearningPanel: true,
            }));
          } catch (error) {
            console.error('Error updating progress:', error);
            setGameState(prevState => ({
              ...prevState,
              cards: finalCards,
              firstCard: null,
              secondCard: null,
              score: prevState.score + 1,
            }));
          }
        } else {
          setGameState(prevState => ({
            ...prevState,
            cards: finalCards,
            firstCard: null,
            secondCard: null,
          }));
        }
      }, 1000);
    }
  };

  return (
    <Stack direction="column" gap={8} p={8} align="center">
      <Text fontSize="4xl" fontWeight="bold" color="blue.600">
        German Word Game
      </Text>
      
      <Stack direction="row" gap={8} justify="center" wrap="wrap">
        <Text fontSize="2xl" fontWeight="medium" color="green.600">
          Score: {gameState.score}
        </Text>
        <Text fontSize="2xl" fontWeight="medium" color="gray.600">
          Moves: {gameState.moves}
        </Text>
        <Stack direction="row" gap={4}>
          {(['easy', 'medium', 'hard'] as const).map((difficulty) => (
            <Button
              key={difficulty}
              colorScheme={difficulty === gameState.difficulty ? 'blue' : 'gray'}
              size="lg"
              onClick={() => initializeGame(difficulty)}
              _hover={{ transform: 'scale(1.05)' }}
              transition="all 0.2s"
            >
              {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
            </Button>
          ))}
        </Stack>
      </Stack>

      {gameState.progress?.suggestions && gameState.progress.suggestions.length > 0 && (
        <Stack direction="row" gap={4} wrap="wrap" justify="center">
          {gameState.progress.suggestions.map((suggestion, index) => (
            <Text key={index} color="purple.600" fontSize="lg">
              💡 {suggestion}
            </Text>
          ))}
        </Stack>
      )}

      {gameState.showLearningPanel && (
        <LearningPanel
          matchedWords={gameState.matchedWords}
          onClose={() => setGameState(prev => ({ ...prev, showLearningPanel: false }))}
        />
      )}

      <Grid
        templateColumns={{
          base: 'repeat(2, 1fr)',
          md: 'repeat(3, 1fr)',
          lg: 'repeat(4, 1fr)'
        }}
        gap={6}
        maxW="1000px"
        w="100%"
        p={4}
      >
        {gameState.cards.map(card => (
          <WordCard
            key={card.id}
            word={card.word}
            isFlipped={card.isFlipped}
            isMatched={card.isMatched}
            onClick={() => handleCardClick(card)}
          />
        ))}
      </Grid>
    </Stack>
  );
};
