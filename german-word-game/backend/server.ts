import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { OpenAI } from 'openai';

dotenv.config();

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

interface WordProgress {
    word: string;
    translation: string;
    timesMatched: number;
    lastMatched: Date;
}

interface UserProgress {
    matchedWords: WordProgress[];
    totalMatches: number;
    difficulty: string;
}

const userProgress: Record<string, UserProgress> = {};

// Generate example sentences for matched words
app.post('/api/generate-examples', async (req, res) => {
    try {
        const { words } = req.body;
        const prompt = `Generate two example sentences in German (with English translations) using these German-English word pairs: ${words.map((w: { german: string; english: string }) => `${w.german} (${w.english})`).join(', ')}. For each sentence, also provide:
1. Word-by-word translation
2. IPA pronunciation for key words
3. A mnemonic device to remember the word
Format as JSON.`;

        const completion = await openai.chat.completions.create({
            model: "gpt-4",
            messages: [{ role: "user", content: prompt }],
            response_format: { type: "json_object" },
        });

        res.json(JSON.parse(completion.choices[0].message.content || '{}'));
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Failed to generate examples' });
    }
});

// Generate a mini-story using learned words
app.post('/api/generate-story', async (req, res) => {
    try {
        const { words } = req.body;
        const prompt = `Create a short, engaging story in German (with English translation) using these words: ${words.map((w: { german: string; english: string }) => `${w.german} (${w.english})`).join(', ')}. Include:
1. A title
2. The story (3-4 sentences)
3. Key vocabulary highlights
4. Grammar notes
Format as JSON.`;

        const completion = await openai.chat.completions.create({
            model: "gpt-4",
            messages: [{ role: "user", content: prompt }],
            response_format: { type: "json_object" },
        });

        res.json(JSON.parse(completion.choices[0].message.content || '{}'));
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Failed to generate story' });
    }
});

// Update user progress
app.post('/api/progress', (req, res) => {
    const { userId, matchedPair, difficulty } = req.body;
    
    if (!userProgress[userId]) {
        userProgress[userId] = {
            matchedWords: [],
            totalMatches: 0,
            difficulty,
        };
    }

    const progress = userProgress[userId];
    const now = new Date();

    // Update matched words
    for (const word of [matchedPair.german, matchedPair.english]) {
        const existingWord = progress.matchedWords.find(w => w.word === word);
        if (existingWord) {
            existingWord.timesMatched++;
            existingWord.lastMatched = now;
        } else {
            progress.matchedWords.push({
                word,
                translation: word === matchedPair.german ? matchedPair.english : matchedPair.german,
                timesMatched: 1,
                lastMatched: now,
            });
        }
    }

    progress.totalMatches++;

    // Generate learning insights
    const insights = generateInsights(progress);
    res.json({ progress, insights });
});

function generateInsights(progress: UserProgress) {
    const now = new Date();
    const insights = {
        needsReview: [] as string[],
        mastered: [] as string[],
        suggestions: [] as string[],
    };

    // Find words that need review (not seen in last 3 days)
    progress.matchedWords.forEach(word => {
        const daysSinceLastMatch = (now.getTime() - new Date(word.lastMatched).getTime()) / (1000 * 60 * 60 * 24);
        
        if (daysSinceLastMatch > 3) {
            insights.needsReview.push(word.word);
        }
        
        if (word.timesMatched >= 5) {
            insights.mastered.push(word.word);
        }
    });

    // Generate suggestions based on performance
    if (insights.needsReview.length > 5) {
        insights.suggestions.push("Consider reviewing older words before learning new ones");
    }

    if (progress.totalMatches > 50 && progress.difficulty === 'easy') {
        insights.suggestions.push("You're doing great! Try increasing the difficulty level");
    }

    return insights;
}

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
