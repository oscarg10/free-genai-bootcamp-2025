-- Make group_id nullable in study_sessions table
PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

-- Create a temporary table with the new schema
CREATE TABLE study_sessions_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER,  -- The group of words being studied (optional)
  study_activity_id INTEGER NOT NULL,  -- The activity performed
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Timestamp of the session
  FOREIGN KEY (group_id) REFERENCES groups(id),
  FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
);

-- Copy data from the old table
INSERT INTO study_sessions_new (id, group_id, study_activity_id, created_at)
SELECT id, group_id, study_activity_id, created_at
FROM study_sessions;

-- Drop the old table
DROP TABLE study_sessions;

-- Rename the new table
ALTER TABLE study_sessions_new RENAME TO study_sessions;

COMMIT;

PRAGMA foreign_keys=ON;
