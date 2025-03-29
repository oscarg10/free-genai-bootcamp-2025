CREATE TABLE IF NOT EXISTS practice_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    german_word TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    word_type TEXT NOT NULL CHECK (word_type IN ('noun', 'verb', 'adjective', 'adverb', 'other')),
    times_incorrect INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_practice_words_session ON practice_words(session_id);
