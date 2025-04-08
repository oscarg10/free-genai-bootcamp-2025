import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import OpenAI from 'openai';

dotenv.config();

const app = express();
const port = process.env.PORT || 3001;

// Initialize OpenAI
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

app.use(cors());
app.use(express.json());

// Helper function to create a chat prompt
const createChatPrompt = (context: string, question: string): Array<OpenAI.Chat.ChatCompletionMessageParam> => {
    return [
        {
            role: "system",
            content: `You are a helpful German language tutor. You help students learn German words and phrases.
                     Current context: ${context}`
        },
        {
            role: "user",
            content: question
        }
    ];
};

// Endpoint for chat responses
app.post('/api/chat', async (req: express.Request, res: express.Response) => {
    try {
        const { question, currentWord } = req.body;
        
        const messages = createChatPrompt(
            `The current word being learned is "${currentWord.german}" which means "${currentWord.english}" in English.`,
            question
        );

        const completion = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages,
            max_tokens: 150,
            temperature: 0.7,
        });

        res.json({ response: completion.choices[0].message.content });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Failed to get response from AI' });
    }
});

// Endpoint for generating new word pairs
app.post('/api/generate-words', async (req: express.Request, res: express.Response) => {
    try {
        const { category, difficulty, count = 5 } = req.body;

        const prompt = `Generate exactly ${count} German-English word pairs for category "${category}" at ${difficulty} difficulty level.

Respond with a JSON object containing a 'pairs' array. Each object in the array must have:
- german: German word (include article for nouns)
- english: English translation
- examples: Array of 2 German example sentences
- difficulty: "${difficulty}"
- category: "${category}"

Example response:
{
  "pairs": [
    {
      "german": "der Hund",
      "english": "the dog",
      "examples": ["Der Hund ist süß.", "Ich habe einen Hund."],
      "difficulty": "${difficulty}",
      "category": "${category}"
    }
  ]
}`;

        const completion = await openai.chat.completions.create({
            model: "gpt-3.5-turbo-1106",
            messages: [
                {
                    role: "system",
                    content: "You are a German language expert that generates JSON responses. Always wrap word pairs in a 'pairs' array property."
                },
                {
                    role: "user",
                    content: prompt
                }
            ],
            max_tokens: 1000,
            temperature: 0.7,
            response_format: { type: "json_object" }
        });

        const content = completion.choices[0].message.content || '{"pairs": []}';
        console.log('OpenAI Response:', content); // Debug log

        // Parse and validate the response
        try {
            const response = JSON.parse(content);
            
            // Validate response structure
            if (!response.pairs || !Array.isArray(response.pairs)) {
                throw new Error('Invalid response format: missing pairs array');
            }

            // Define the type for word pairs
            interface WordPair {
                german: string;
                english: string;
                examples: string[];
                difficulty: string;
                category: string;
            }

            // Validate each word pair
            const validPairs = response.pairs.filter((pair: any): pair is WordPair => {
                return pair && 
                       typeof pair.german === 'string' && 
                       typeof pair.english === 'string' && 
                       Array.isArray(pair.examples) && 
                       pair.examples.length === 2 && 
                       pair.difficulty === difficulty && 
                       pair.category === category;
            });

            if (validPairs.length === 0) {
                throw new Error('No valid word pairs generated');
            }

            res.json(validPairs);
        } catch (error: any) {
            console.error('Failed to parse JSON:', content);
            res.status(500).json({ 
                error: 'Failed to generate valid word pairs',
                details: error?.message || 'Unknown parsing error'
            });
        }
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Failed to generate word pairs' });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
