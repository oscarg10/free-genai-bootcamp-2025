from invoke import task
import os
import sqlite3
import json
from lib.db import db

@task
def init_db(ctx):
  from flask import Flask
  app = Flask(__name__)
  db.init(app)
  print("Database initialized successfully.")

@task
def setup_db(ctx):
    """Initialize the database with tables and sample data"""
    # Remove existing database
    if os.path.exists('words.db'):
        os.remove('words.db')
    
    # Create new database and tables
    conn = sqlite3.connect('words.db')
    conn.row_factory = sqlite3.Row
    
    try:
        # Create all tables in the correct order
        print("Creating tables...")
        table_files = [
            'create_table_words.sql',
            'create_table_groups.sql',
            'create_table_word_groups.sql',
            'create_table_study_activities.sql',
            'create_table_study_sessions.sql',
            'create_table_word_reviews.sql',
            'create_table_word_review_items.sql'
        ]
        
        for file in table_files:
            print(f"Creating table from {file}...")
            with open(f'sql/setup/{file}') as f:
                conn.executescript(f.read())
        
        # Load sample verbs
        print("Loading sample verbs...")
        with open('seed/data_verbs.json') as f:
            verbs_data = json.load(f)
            for verb in verbs_data['verbs']:
                conn.execute('''
                    INSERT INTO words (german, pronunciation, english, word_type, additional_info)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    verb['german'],
                    verb.get('pronunciation'),
                    verb['english'],
                    verb['word_type'],
                    json.dumps(verb.get('additional_info', {}))
                ))
        
        # Insert study activities
        print("Loading study activities...")
        with open('sql/setup/insert_study_activities.sql') as f:
            conn.executescript(f.read())
        
        conn.commit()
        print("Database setup complete!")
    
    except Exception as e:
        conn.rollback()
        print(f"Error setting up database: {str(e)}")
        raise e
    finally:
        conn.close()