import sqlite3
import json
from flask import g
import os
import logging

  # Setup logging
logging.basicConfig(
      level=logging.DEBUG,
      format='%(asctime)s - %(levelname)s - %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S'
  )
logger = logging.getLogger(__name__)

class Db:
  def __init__(self, database_url='sqlite:///data/lang_portal.db'):
    # Extract the database path from the URL
    if database_url.startswith('sqlite:///'):
      self.database = database_url[10:]  # Remove 'sqlite:///'
    else:
      self.database = database_url
    self.connection = None
    
    # Create data directory if it doesn't exist
    data_dir = os.path.dirname(self.database)
    if data_dir and not os.path.exists(data_dir):
      os.makedirs(data_dir)

  def add_practice_word(self, session_id: int, german_word: str, english_translation: str, word_type: str):
    """Add a word to the practice_words table."""
    try:
        logger.info(f"Adding practice word: {german_word} ({english_translation}) for session {session_id}")
        cursor = self.cursor()
        cursor.execute("""
            INSERT INTO practice_words (session_id, german_word, english_translation, word_type)
            VALUES (?, ?, ?, ?)
        """, (session_id, german_word, english_translation, word_type))
        logger.debug(f"SQL query executed with params: {(session_id, german_word, english_translation, word_type)}")
        self.commit()
        last_id = cursor.lastrowid
        logger.info(f"Successfully added practice word with ID: {last_id}")
        return last_id
    except Exception as e:
        logger.error(f"Failed to add practice word: {str(e)}")
        self.rollback()
        raise e
  def get(self):
    if 'db' not in g:
      # Ensure we're using an absolute path
      db_path = os.path.abspath(self.database)
      g.db = sqlite3.connect(db_path)
      g.db.row_factory = sqlite3.Row  # Return rows as dictionaries
      # Enable foreign key support
      g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

  def __enter__(self):
    return self.get()

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type is not None:
      # An error occurred, rollback
      self.get().rollback()
    self.close()

  def commit(self):
    self.get().commit()

  def rollback(self):
    self.get().rollback()

  def begin_transaction(self):
    self.get().execute('BEGIN TRANSACTION')

  def cursor(self):
    # Ensure the connection is valid before getting a cursor
    connection = self.get()
    return connection.cursor()

  def close(self):
    db = g.pop('db', None)
    if db is not None:
      db.close()

  # Function to load SQL from a file
  def sql(self, filepath):
    with open('sql/' + filepath, 'r') as file:
      return file.read()

  # Function to load the words from a JSON file
  def load_json(self, filepath):
    with open(filepath, 'r') as file:
      return json.load(file)

  def setup_tables(self,cursor):
    # Create the necessary tables
    cursor.execute(self.sql('setup/create_table_words.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_table_word_reviews.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_table_word_review_items.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_table_groups.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_table_word_groups.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_table_study_activities.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_table_study_sessions.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_table_practice_words.sql'))
    self.get().commit()

    cursor.execute(self.sql('setup/create_index_practice_words.sql'))
    self.get().commit()

  def import_study_activities_json(self,cursor,data_json_path):
    study_activities = self.load_json(data_json_path)
    # Clear existing activities
    cursor.execute('DELETE FROM study_activities')
    for activity in study_activities:
      cursor.execute('''
      INSERT INTO study_activities (name,url,preview_url) VALUES (?,?,?)
      ''', (activity['name'],activity['url'],activity['preview_url']))
    self.get().commit()
    print(f"Successfully imported {len(study_activities)} study activities")

  def import_word_json(self,cursor,group_name,data_json_path):
      # Insert a new group
      cursor.execute('''
        INSERT INTO groups (name) VALUES (?)
      ''', (group_name,))
      self.get().commit()

      # Get the ID of the group
      cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
      group_id = cursor.fetchone()[0]

      # Load and parse JSON data
      data = self.load_json(data_json_path)
      # Get the word list based on group name
      word_type = group_name.lower().split()[-1]  # 'Core Verbs' -> 'verbs'
      words = data.get(word_type, [])

      for word in words:
        # Insert the word into the words table
        cursor.execute('''
          INSERT INTO words (german, pronunciation, english, article, word_type, additional_info) 
          VALUES (?, ?, ?, ?, ?, ?)
        ''', (
          word['german'], 
          word.get('pronunciation'), 
          word['english'], 
          word.get('article'), 
          word['word_type'],
          json.dumps(word.get('additional_info', {}))
        ))
        
        # Get the last inserted word's ID
        word_id = cursor.lastrowid

        # Insert the word-group relationship into word_groups table
        cursor.execute('''
          INSERT INTO word_groups (word_id, group_id) VALUES (?, ?)
        ''', (word_id, group_id))
      self.get().commit()

      # Update the words_count in the groups table
      cursor.execute('''
        UPDATE groups
        SET words_count = (
          SELECT COUNT(*) FROM word_groups WHERE group_id = ?
        )
        WHERE id = ?
      ''', (group_id, group_id))

      self.get().commit()

      print(f"Successfully added {len(words)} words to the '{group_name}' group.")

  def get_practice_words(self, session_id: int) -> list:
    """Get all practice words for a session."""
    try:
      cursor = self.cursor()
      cursor.execute("""
        SELECT german_word, english_translation, word_type, times_incorrect, created_at
        FROM practice_words
        WHERE session_id = ?
        ORDER BY times_incorrect DESC, created_at DESC
      """, (session_id,))
      return cursor.fetchall()
    except Exception as e:
      print(f"Error getting practice words: {e}")
      return []

  # Initialize the database with sample data
  def init(self, app):
    with app.app_context():
      cursor = self.cursor()
      self.setup_tables(cursor)
      self.import_word_json(
        cursor=cursor,
        group_name='Core Verbs',
        data_json_path='seed/data_verbs.json'
      )
      self.import_word_json(
        cursor=cursor,
        group_name='Core Adjectives',
        data_json_path='seed/data_adjectives.json'
      )

      self.import_study_activities_json(
        cursor=cursor,
        data_json_path='seed/study_activities.json'
      )

# Create an instance of the Db class
db = Db()
