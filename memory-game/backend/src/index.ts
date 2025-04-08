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
const createChatPrompt = (context: string, question: string) => {
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

        const prompt = `Generate ${count} German-English word pairs for the category "${category}" at ${difficulty} difficulty level.
                       Format the response as a JSON array of objects with properties:
                       - german: the German word with article if noun
                       - english: the English translation
                       - examples: array of 2 example German sentences using the word
                       - difficulty: "${difficulty}"
                       - category: "${category}"`;

        const completion = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [
                {
                    role: "system",
                    content: "You are a German language expert. Provide accurate translations and natural example sentences."
                },
                {
                    role: "user",
                    content: prompt
                }
            ],
            max_tokens: 500,
            temperature: 0.7,
        });

        // Parse the response and validate it's proper JSON
        const wordPairs = JSON.parse(completion.choices[0].message.content || '[]');
        res.json(wordPairs);
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Failed to generate word pairs' });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
