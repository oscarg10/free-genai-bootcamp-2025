import React from 'react';
import {
    Box,
    Heading,
    VStack,
    Text,
    Grid,
    GridItem
} from '@chakra-ui/react';

interface VocabularyItem {
    word: string;
    context: string;
}

interface VocabularyListProps {
    vocabulary: VocabularyItem[];
}

const VocabularyList: React.FC<VocabularyListProps> = ({ vocabulary }) => {
    return (
        <Box width="100%">
            <Heading size="md" mb={4}>Vocabulary</Heading>
            <VStack gap={4} align="stretch">
                <Grid templateColumns="1fr 2fr" gap={4} p={4} bg="gray.50" borderRadius="md">
                    <GridItem fontWeight="bold">
                        <Text>German Word</Text>
                    </GridItem>
                    <GridItem fontWeight="bold">
                        <Text>Context</Text>
                    </GridItem>
                </Grid>
                {vocabulary.map((item, index) => (
                    <Grid 
                        key={index} 
                        templateColumns="1fr 2fr" 
                        gap={4} 
                        p={4} 
                        bg="white" 
                        borderRadius="md" 
                        boxShadow="sm"
                    >
                        <GridItem>
                            <Text fontWeight="bold">{item.word}</Text>
                        </GridItem>
                        <GridItem>
                            <Text>{item.context}</Text>
                        </GridItem>
                    </Grid>
                ))}
            </VStack>
        </Box>
    );
};

export default VocabularyList;
