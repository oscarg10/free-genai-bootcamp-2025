CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  words_count INTEGER DEFAULT 0,  -- Counter cache for the number of words in the group
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(name)  -- Prevent duplicate groups
);