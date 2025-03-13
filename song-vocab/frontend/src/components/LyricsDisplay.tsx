import React from 'react';
import { Box, Text, Heading } from '@chakra-ui/react';

interface LyricsDisplayProps {
    lyrics: string;
}

const LyricsDisplay: React.FC<LyricsDisplayProps> = ({ lyrics }) => {
    return (
        <Box
            p={4}
            borderWidth={1}
            borderRadius="md"
            width="100%"
            maxHeight="400px"
            overflowY="auto"
        >
            <Heading size="md" mb={4}>Lyrics</Heading>
            <Text whiteSpace="pre-wrap">{lyrics}</Text>
        </Box>
    );
};

export default LyricsDisplay;
