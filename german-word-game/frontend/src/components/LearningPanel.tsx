import { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  Text,
  Button,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Spinner,
  useToast,
} from '@chakra-ui/react';

interface Word {
  german: string;
  english: string;
}

interface Example {
  german: string;
  english: string;
  wordByWord: string;
  pronunciation: string;
  mnemonic: string;
}

interface Story {
  title: string;
  german: string;
  english: string;
  vocabulary: string[];
  grammarNotes: string[];
}

interface LearningPanelProps {
  matchedWords: Word[];
  onClose: () => void;
}

export const LearningPanel = ({ matchedWords, onClose }: LearningPanelProps) => {
  const [examples, setExamples] = useState<Example[]>([]);
  const [story, setStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const generateExamples = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:3001/api/generate-examples', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ words: matchedWords }),
      });
      
      if (!response.ok) throw new Error('Failed to generate examples');
      
      const data = await response.json();
      setExamples(data.examples);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to generate examples',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  const generateStory = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:3001/api/generate-story', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ words: matchedWords }),
      });
      
      if (!response.ok) throw new Error('Failed to generate story');
      
      const data = await response.json();
      setStory(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to generate story',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (matchedWords.length > 0) {
      generateExamples();
    }
  }, [matchedWords]);

  return (
    <Box
      position="fixed"
      right="20px"
      top="20px"
      bg="white"
      boxShadow="xl"
      borderRadius="lg"
      p={6}
      maxW="400px"
      maxH="90vh"
      overflowY="auto"
    >
      <VStack spacing={4} align="stretch">
        <Text fontSize="2xl" fontWeight="bold" color="blue.600">
          Learning Panel
        </Text>

        {loading ? (
          <Spinner />
        ) : (
          <>
            <Accordion allowMultiple>
              {examples.map((example, index) => (
                <AccordionItem key={index}>
                  <AccordionButton>
                    <Box flex="1" textAlign="left">
                      Example {index + 1}
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel>
                    <VStack align="start" spacing={2}>
                      <Text fontWeight="medium">German:</Text>
                      <Text>{example.german}</Text>
                      <Text fontWeight="medium">English:</Text>
                      <Text>{example.english}</Text>
                      <Text fontWeight="medium">Word by Word:</Text>
                      <Text>{example.wordByWord}</Text>
                      <Text fontWeight="medium">Pronunciation:</Text>
                      <Text fontFamily="monospace">{example.pronunciation}</Text>
                      <Text fontWeight="medium">Mnemonic:</Text>
                      <Text>{example.mnemonic}</Text>
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              ))}

              {story && (
                <AccordionItem>
                  <AccordionButton>
                    <Box flex="1" textAlign="left">
                      Story
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel>
                    <VStack align="start" spacing={2}>
                      <Text fontWeight="bold">{story.title}</Text>
                      <Text fontWeight="medium">German:</Text>
                      <Text>{story.german}</Text>
                      <Text fontWeight="medium">English:</Text>
                      <Text>{story.english}</Text>
                      <Text fontWeight="medium">Key Vocabulary:</Text>
                      {story.vocabulary.map((word, i) => (
                        <Text key={i}>• {word}</Text>
                      ))}
                      <Text fontWeight="medium">Grammar Notes:</Text>
                      {story.grammarNotes.map((note, i) => (
                        <Text key={i}>• {note}</Text>
                      ))}
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              )}
            </Accordion>

            <Button
              colorScheme="blue"
              onClick={generateStory}
              isDisabled={matchedWords.length < 3}
            >
              Generate Story
            </Button>

            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </>
        )}
      </VStack>
    </Box>
  );
};
