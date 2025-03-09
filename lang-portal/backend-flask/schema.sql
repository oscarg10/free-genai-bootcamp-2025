-- Create words table
CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  german TEXT NOT NULL,
  english TEXT NOT NULL,
  word_type TEXT NOT NULL CHECK (word_type IN ('noun', 'verb', 'adjective', 'adverb', 'other')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create group_words table for associating words with groups
CREATE TABLE IF NOT EXISTS group_words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER NOT NULL,
  word_id INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (group_id) REFERENCES groups (id),
  FOREIGN KEY (word_id) REFERENCES words (id),
  UNIQUE (group_id, word_id)
);

-- Insert some sample words
INSERT INTO words (german, english, word_type) VALUES
  ('der Hund', 'dog', 'noun'),
  ('die Katze', 'cat', 'noun'),
  ('groß', 'big', 'adjective'),
  ('klein', 'small', 'adjective'),
  ('laufen', 'run', 'verb'),
  ('springen', 'jump', 'verb');

-- Associate words with the first group
INSERT INTO group_words (group_id, word_id) 
SELECT 1, id FROM words;
