import sqlite3
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with schema and initial data."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("../../data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        db_path = data_dir / "lang_portal.db"
        
        # Delete old database if it exists
        if db_path.exists():
            logger.info("Deleting old database")
            db_path.unlink()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            try:
                try:
                    # Begin transaction
                    conn.execute("BEGIN TRANSACTION")
                    
                    # Read and execute schema first
                    schema_path = Path(__file__).parent.parent.parent / "schema.sql"
                    with open(schema_path) as f:
                        schema_sql = f.read()
                        cursor.executescript(schema_sql)
                    
                    # Insert initial study activities
                    cursor.execute("""
                        INSERT OR IGNORE INTO study_activities (id, name, url, preview_url) VALUES 
                        (1, 'Writing Practice', 'http://localhost:8080/writing', '/assets/study_activities/writing-practice.png'),
                        (2, 'Song Vocabulary', 'http://localhost:8000', '/assets/study_activities/song-vocab.png'),
                        (3, 'Word Memorization', 'http://localhost:7860', '/assets/study_activities/word-memorization-preview.png'),
                        (4, 'Listening Practice', 'http://localhost:8501', '/assets/study_activities/listening-practice.png')
                    """)
                    
                    # Insert initial groups
                    cursor.execute("""
                        INSERT OR IGNORE INTO groups (name, words_count) VALUES 
                        ('Beginner German', 0),
                        ('Intermediate German', 0),
                        ('Advanced German', 0)
                    """)
                    
                    # Commit all changes
                    conn.commit()
                    logger.info("Database initialized successfully")
                    
                except Exception as e:
                    conn.rollback()
                    raise e
                
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
