import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, WordPair } from '../types';
import './LearningAssistant.css';

interface LearningAssistantProps {
    currentCard?: WordPair;
}

export const LearningAssistant: React.FC<LearningAssistantProps> = ({ currentCard }) => {
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            text: "Hi Deutsch Student! I'm your German learning assistant. I can help you with:\n- Word meanings and translations\n- Pronunciation tips\n- Grammar explanations\n- Example sentences\n- Usage in different contexts\n\nAsk me anything about German words and grammar!",
            type: 'bot',
            timestamp: Date.now()
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const generateResponse = async (question: string): Promise<string> => {
        try {
            const response = await fetch('http://localhost:3001/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    currentWord: currentCard,
                    messageHistory: messages
                        .slice(-6) // Keep last 6 messages for context
                        .map(msg => ({
                            role: msg.type === 'user' ? 'user' : 'assistant',
                            content: msg.text
                        }))
                })
            });

            if (!response.ok) throw new Error('Failed to get response');
            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Chat error:', error);
            return 'Sorry, I had trouble understanding that. Could you try rephrasing your question?';
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            text: input,
            type: 'user',
            timestamp: Date.now()
        };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await generateResponse(input);
            const botMessage: ChatMessage = {
                text: response,
                type: 'bot',
                timestamp: Date.now()
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error('Error:', error);
            const errorMessage: ChatMessage = {
                text: 'Sorry, I encountered an error. Please try again.',
                type: 'bot',
                timestamp: Date.now()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="learning-assistant">
            <div className="chat-messages">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`message ${message.type}`}
                    >
                        {message.text.split('\n').map((line, i) => (
                            <p key={i}>{line}</p>
                        ))}
                    </div>
                ))}
                {isLoading && (
                    <div className="message bot">
                        <p>Thinking...</p>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <form onSubmit={handleSubmit} className="chat-input">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about German words, grammar, or pronunciation..."
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading}>
                    {isLoading ? '...' : 'Send'}
                </button>
            </form>
        </div>
    );
};
