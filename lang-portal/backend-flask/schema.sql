-- Create words table
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    german TEXT NOT NULL,
    pronunciation TEXT,
    english TEXT NOT NULL,
    article TEXT CHECK (article IN ('der', 'die', 'das') OR article IS NULL),
    word_type TEXT NOT NULL CHECK (word_type IN ('noun', 'verb', 'adjective', 'adverb', 'other')),
    additional_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create word reviews table
CREATE TABLE IF NOT EXISTS word_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    correct_count INTEGER DEFAULT 0,
    wrong_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (word_id) REFERENCES words(id)
);

-- Create study activities table
CREATE TABLE IF NOT EXISTS study_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    preview_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drop and recreate groups table
DROP TABLE IF EXISTS groups;
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    words_count INTEGER DEFAULT 0,
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

-- Create word groups table
CREATE TABLE IF NOT EXISTS word_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create practice words table
CREATE TABLE IF NOT EXISTS practice_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    german_word TEXT NOT NULL,
    english_translation TEXT NOT NULL,
    word_type TEXT NOT NULL CHECK (word_type IN ('noun', 'verb', 'adjective', 'adverb', 'other')),
    times_incorrect INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
);

-- Create word group assignments table
CREATE TABLE IF NOT EXISTS word_group_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (word_id) REFERENCES practice_words(id),
    FOREIGN KEY (group_id) REFERENCES word_groups(id),
    UNIQUE(word_id, group_id)
);

-- Create indices for better performance
CREATE INDEX IF NOT EXISTS idx_vocabulary_session ON vocabulary(session_id);
CREATE INDEX IF NOT EXISTS idx_practice_words_session ON practice_words(session_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_song ON vocabulary(song_id);
CREATE INDEX IF NOT EXISTS idx_sessions_group ON study_sessions(group_id);
CREATE INDEX IF NOT EXISTS idx_sessions_activity ON study_sessions(study_activity_id);
CREATE INDEX IF NOT EXISTS idx_word_group_assignments_word ON word_group_assignments(word_id);
CREATE INDEX IF NOT EXISTS idx_word_group_assignments_group ON word_group_assignments(group_id);

-- Insert initial word groups
INSERT OR IGNORE INTO word_groups (name, description) VALUES
    ('Basic Vocabulary', 'Essential everyday words'),
    ('Travel', 'Words related to traveling and transportation'),
    ('Food & Drink', 'Culinary and dining vocabulary'),
    ('Family', 'Words for family members and relationships'),
    ('Numbers & Time', 'Numerical expressions and time-related words'),
    ('Colors & Shapes', 'Words describing colors and shapes'),
    ('Weather', 'Weather-related vocabulary'),
    ('Professions', 'Job titles and work-related words'),
    ('Emotions', 'Words expressing feelings and emotions'),
    ('Body & Health', 'Anatomy and health-related terms');

-- Create word review items table
CREATE TABLE IF NOT EXISTS word_review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_session_id INTEGER NOT NULL,
    word_id INTEGER,
    practice_word_id INTEGER,
    is_correct BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (study_session_id) REFERENCES study_sessions(id),
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (practice_word_id) REFERENCES practice_words(id),
    CHECK ((word_id IS NULL AND practice_word_id IS NOT NULL) OR (word_id IS NOT NULL AND practice_word_id IS NULL))
);
