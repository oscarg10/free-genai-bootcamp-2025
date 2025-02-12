import sqlite3
import os
from pathlib import Path

def init_db():
    # Get the absolute path to the database file
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / 'words.db'
    
    print(f"Initializing database at: {db_path}")
    
    # Connect to database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute all setup SQL files in order
    setup_dir = base_dir / 'sql' / 'setup'
    sql_files = [
        'create_table_words.sql',
        'create_table_groups.sql',
        'create_table_word_groups.sql',
        'create_table_word_reviews.sql',
        'create_table_study_sessions.sql',
        'create_table_study_activities.sql',
        'create_table_word_review_items.sql'
    ]
    
    for sql_file in sql_files:
        print(f"Executing {sql_file}...")
        with open(setup_dir / sql_file, 'r') as f:
            cursor.executescript(f.read())
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()