import React from 'react';
import {
    ChakraProvider,
    Container,
    VStack,
    Heading,
} from '@chakra-ui/react';
import SongSearch from './components/SongSearch';
import VocabularyList from './components/VocabularyList';
import LyricsDisplay from './components/LyricsDisplay';

interface SongData {
    lyrics: string;
    vocabulary: Array<{
        word: string;
        context: string;
    }>;
}

const App: React.FC = () => {
    const [songData, setSongData] = React.useState<SongData | null>(null);

    return (
        <ChakraProvider>
            <Container maxW="container.xl" py={8}>
                <VStack gap={8} align="stretch">
                    <Heading>German Song Vocabulary Extractor</Heading>
                    <SongSearch onSongFound={setSongData} />
                    {songData && (
                        <>
                            <LyricsDisplay lyrics={songData.lyrics} />
                            <VocabularyList vocabulary={songData.vocabulary} />
                        </>
                    )}
                </VStack>
            </Container>
        </ChakraProvider>
    );
};

export default App;
