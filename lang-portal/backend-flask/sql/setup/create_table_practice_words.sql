CREATE TABLE IF NOT EXISTS practice_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    german_word TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    word_type TEXT NOT NULL,
    times_incorrect INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
);
