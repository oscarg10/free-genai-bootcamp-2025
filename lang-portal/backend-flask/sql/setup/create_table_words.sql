CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  german TEXT NOT NULL,
  pronunciation TEXT,
  english TEXT NOT NULL,
  article TEXT,  -- der/die/das for nouns
  word_type TEXT NOT NULL,  -- noun, verb, adjective, etc.
  additional_info TEXT  -- Store additional info as JSON string (e.g., verb conjugations, plural forms)
);