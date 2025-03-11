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
                schema_path = Path("sql/setup/schema.sql")
                with open(schema_path) as f:
                    cursor.executescript(f.read())
                
                # Clear existing study activities
                cursor.execute("DELETE FROM study_activities")
                
                # Insert initial study activities
                cursor.execute("""
                    INSERT INTO study_activities (id, name, url, preview_url) VALUES 
                    (1, 'Typing Tutor', 'http://localhost:8080', '/assets/study_activities/typing-tutor.png'),
                    (2, 'Writing Practice', 'http://localhost:8080/writing', '/assets/study_activities/writing-practice.png'),
                    (3, 'Song Vocabulary', 'http://localhost:8000', '/assets/study_activities/song-vocab.png')
                """)
                
                # Insert initial groups
                cursor.execute("""
                    INSERT INTO groups (name) VALUES 
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
