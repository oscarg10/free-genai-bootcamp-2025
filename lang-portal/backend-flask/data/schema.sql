-- Create study activities table
CREATE TABLE IF NOT EXISTS study_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    preview_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create groups table
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create study sessions table
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    study_activity_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
);

-- Create songs table
CREATE TABLE IF NOT EXISTS songs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    lyrics TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create vocabulary table
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    song_id TEXT,
    word TEXT NOT NULL,
    song_title TEXT NOT NULL,
    artist TEXT NOT NULL,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id),
    FOREIGN KEY (song_id) REFERENCES songs(id)
);

-- Create practice words table
CREATE TABLE IF NOT EXISTS practice_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    german_word TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    word_type TEXT NOT NULL CHECK (word_type IN ('noun', 'verb', 'adjective', 'adverb', 'other')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
);

-- Create indices for better performance
CREATE INDEX IF NOT EXISTS idx_vocabulary_session ON vocabulary(session_id);
CREATE INDEX IF NOT EXISTS idx_practice_words_session ON practice_words(session_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_song ON vocabulary(song_id);
CREATE INDEX IF NOT EXISTS idx_sessions_group ON study_sessions(group_id);
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON study_sessions(study_activity_id);

-- Create word review items table
CREATE TABLE IF NOT EXISTS word_review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_session_id INTEGER NOT NULL,
    word_id INTEGER,
    correct BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
);

-- Create index for word reviews
CREATE INDEX IF NOT EXISTS idx_word_reviews_session ON word_review_items(study_session_id);


