import { Box, Text } from '@chakra-ui/react';
import { motion } from 'framer-motion';

interface WordCardProps {
  word: string;
  isFlipped: boolean;
  isMatched: boolean;
  onClick: () => void;
}

const MotionBox = motion(Box);

export const WordCard = ({ word, isFlipped, isMatched, onClick }: WordCardProps) => {
  return (
    <MotionBox
      as="button"
      w="full"
      h="120px"
      bg={isMatched ? "green.100" : isFlipped ? "blue.100" : "gray.100"}
      borderRadius="lg"
      boxShadow="md"
      display="flex"
      alignItems="center"
      justifyContent="center"
      cursor={isMatched ? "default" : "pointer"}
      onClick={!isMatched ? onClick : undefined}
      whileHover={!isMatched ? { scale: 1.05, boxShadow: "lg" } : {}}
      whileTap={!isMatched ? { scale: 0.95 } : {}}
      transition={{ duration: 0.2 }}
      p={4}
    >
      <Text
        fontSize="2xl"
        fontWeight="bold"
        color={isMatched ? "green.600" : isFlipped ? "blue.600" : "gray.600"}
      >
        {isFlipped || isMatched ? word : "?"}
      </Text>
    </MotionBox>
  );
};
