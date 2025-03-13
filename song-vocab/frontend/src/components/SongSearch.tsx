import React from 'react';
import {
    VStack,
    Input,
    Button,
    Box,
    FormControl,
    FormLabel,
    useToast
} from '@chakra-ui/react';
import axios from 'axios';

interface SongSearchProps {
    onSongFound: (data: {
        lyrics: string;
        vocabulary: Array<{
            word: string;
            context: string;
        }>;
    }) => void;
}

const SongSearch: React.FC<SongSearchProps> = ({ onSongFound }) => {
    const [title, setTitle] = React.useState('');
    const [artist, setArtist] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const toast = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await axios.post('http://localhost:8000/api/agent', {
                song_title: title,
                artist: artist
            });

            onSongFound(response.data);
            toast({
                title: 'Success',
                description: 'Found song vocabulary!',
                status: 'success',
                duration: 3000,
                isClosable: true,
                position: 'top-right',
            });
        } catch (error: any) {
            toast({
                title: 'Error',
                description: error.response?.data?.detail || 'Failed to find song',
                status: 'error',
                duration: 5000,
                isClosable: true,
                position: 'top-right',
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box as="form" onSubmit={handleSubmit} width="100%">
            <VStack gap={4} align="stretch">
                <FormControl>
                    <FormLabel>Song Title</FormLabel>
                    <Input
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Enter song title"
                    />
                </FormControl>
                <FormControl>
                    <FormLabel>Artist</FormLabel>
                    <Input
                        value={artist}
                        onChange={(e) => setArtist(e.target.value)}
                        placeholder="Enter artist name"
                    />
                </FormControl>
                <Button
                    type="submit"
                    colorScheme="blue"
                    isLoading={loading}
                    width="100%"
                >
                    Search Song
                </Button>
            </VStack>
        </Box>
    );
};

export default SongSearch;
