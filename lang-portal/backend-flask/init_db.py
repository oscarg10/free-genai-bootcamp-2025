import sqlite3
import os
import json
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
        'create_table_word_review_items.sql',
        'insert_study_activities.sql'  # Add this line to execute our inserts
    ]
    
    for sql_file in sql_files:
        print(f"Executing {sql_file}...")
        with open(setup_dir / sql_file, 'r') as f:
            cursor.executescript(f.read())
    # Insert sample data
    print("Inserting sample data...")
    
    # Insert a sample group
    cursor.execute("""
    INSERT INTO groups (name, words_count) VALUES (?, ?)
    """, ('Basic German Vocabulary', 0))
    group_id = cursor.lastrowid
    
    # Insert sample words
    sample_words = [
        ('der Hund', 'the dog', 'noun', 'masculine'),
        ('das Buch', 'the book', 'noun', 'neuter'),
        ('die Katze', 'the cat', 'noun', 'feminine'),
        ('spielen', 'to play', 'verb', None),
        ('schön', 'beautiful', 'adjective', None)
    ]
    
    for german, english, word_type, gender in sample_words:
        # Insert word
        cursor.execute("""
        INSERT INTO words (german, english, word_type, additional_info)
        VALUES (?, ?, ?, ?)
        """, (german, english, word_type, json.dumps({'gender': gender}) if gender else '{}'))
        word_id = cursor.lastrowid
        
        # Link word to group
        cursor.execute("""
        INSERT INTO word_groups (word_id, group_id)
        VALUES (?, ?)
        """, (word_id, group_id))
    
    # Update group word count
    cursor.execute("""
    UPDATE groups 
    SET words_count = (
        SELECT COUNT(*) 
        FROM word_groups 
        WHERE group_id = ?
    )
    WHERE id = ?
    """, (group_id, group_id))

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()