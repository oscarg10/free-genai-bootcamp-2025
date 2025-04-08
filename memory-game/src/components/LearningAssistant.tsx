import { useState, useRef, useEffect } from 'react';
import { ChatMessage, WordPair } from '../types';
import './LearningAssistant.css';

interface LearningAssistantProps {
    currentCard?: WordPair;
}

export const LearningAssistant = ({ currentCard }: LearningAssistantProps) => {
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            text: "Hi! I'm your learning assistant. Ask me about any German word you see, or type 'help' for more options!",
            type: 'bot',
            timestamp: Date.now()
        }
    ]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const generateResponse = (question: string): string => {
        const lowerQuestion = question.toLowerCase();
        
        if (lowerQuestion === 'help') {
            return `Here's what you can ask me:
                   - "How do I use [word]?"
                   - "Show examples for [word]"
                   - "What does [word] mean?"`;
        }

        if (currentCard) {
            if (lowerQuestion.includes('use') || lowerQuestion.includes('example')) {
                return `Here are some examples using "${currentCard.german}":
                       ${currentCard.examples.join('\\n')}`;
            }
            if (lowerQuestion.includes('mean')) {
                return `"${currentCard.german}" means "${currentCard.english}" in English.`;
            }
        }

        return "I'm not sure about that. Try asking about the current word you're learning, or type 'help' for options!";
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage: ChatMessage = {
            text: input,
            type: 'user',
            timestamp: Date.now()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');

        const response = await generateResponse(input);
        const botMessage: ChatMessage = {
            text: response,
            type: 'bot',
            timestamp: Date.now()
        };

        setMessages(prev => [...prev, botMessage]);
    };

    return (
        <div className="learning-assistant">
            <div className="chat-messages">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`message ${message.type}`}
                    >
                        {message.text}
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
            <form onSubmit={handleSubmit} className="chat-input">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about a word..."
                />
                <button type="submit">Send</button>
            </form>
        </div>
    );
};
