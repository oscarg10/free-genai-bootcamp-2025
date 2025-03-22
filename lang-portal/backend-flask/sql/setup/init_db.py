import sqlite3
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with schema and initial data."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        db_path = data_dir / "lang_portal.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            try:
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")
                
                # Read and execute schema
                schema_path = Path("data/schema.sql")
                with open(schema_path) as f:
                    cursor.executescript(f.read())
                
                
                # Insert initial study activities if they don't exist
                cursor.execute("""
                    INSERT OR IGNORE INTO study_activities (id, name, url, preview_url) VALUES 
                    (1, 'Writing Practice', 'http://localhost:8080/writing', '/assets/study_activities/writing-practice.png'),
                    (2, 'Song Vocabulary', 'http://localhost:8000', '/assets/study_activities/song-vocab.png'),
                    (3, 'Word Memorization', 'http://localhost:7860', '/assets/study_activities/word-memorization-preview.png'),
                    (4, 'Listening Practice', 'http://localhost:8501', '/assets/study_activities/listening-practice.png')
                """)
                
                # Insert initial groups
                cursor.execute("""
                    INSERT OR IGNORE INTO groups (name) VALUES 
                    ('Beginner German'),
                    ('Intermediate German'),
                    ('Advanced German')
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                
    except Exception as e:
        error_msg = f"Failed to initialize database: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
