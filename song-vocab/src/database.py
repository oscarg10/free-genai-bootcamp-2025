import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from src.exceptions import StorageError

logger = logging.getLogger(__name__)

# Define the database path relative to the data directory
DB_PATH = Path("data/vocab.db")

def init_db():
    """Initialize the database and create necessary tables.
    
    Raises:
        StorageError: If database initialization fails
    """
    try:
        # Create data directory if it doesn't exist
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                # Create vocabulary table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vocabulary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT NOT NULL,
                        song_title TEXT NOT NULL,
                        artist TEXT NOT NULL,
                        context TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create songs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS songs (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        artist TEXT NOT NULL,
                        lyrics TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
            finally:
                cursor.close()
                
    except Exception as e:
        error_msg = f"Failed to initialize database: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg)

def save_vocabulary_items(items: List[Dict[str, str]], song_id: str, song_title: str, artist: str) -> None:
    """Save multiple vocabulary items for a song.
    
    Args:
        items: List of vocabulary items with word and context
        song_id: Unique identifier for the song
        song_title: Title of the song
        artist: Name of the artist
        
    Raises:
        StorageError: If saving fails
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Insert vocabulary items
                for item in items:
                    cursor.execute(
                        "INSERT INTO vocabulary (word, song_title, artist, context) VALUES (?, ?, ?, ?)",
                        (item["word"], song_title, artist, item["context"])
                    )
                
                conn.commit()
                logger.info(f"Saved {len(items)} vocabulary items for song {song_title}")
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                
    except Exception as e:
        error_msg = f"Failed to save vocabulary items: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg)

def save_song(song_id: str, title: str, artist: str, lyrics: str) -> None:
    """Save song information to the database.
    
    Args:
        song_id: Unique identifier for the song
        title: Title of the song
        artist: Name of the artist
        lyrics: Full lyrics of the song
        
    Raises:
        StorageError: If saving fails
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO songs (id, title, artist, lyrics) VALUES (?, ?, ?, ?)",
                    (song_id, title, artist, lyrics)
                )
                conn.commit()
                logger.info(f"Saved song {title} by {artist} with ID {song_id}")
                
            finally:
                cursor.close()
                
    except sqlite3.IntegrityError:
        # Song already exists, update it
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "UPDATE songs SET lyrics = ?, title = ?, artist = ? WHERE id = ?",
                        (lyrics, title, artist, song_id)
                    )
                    conn.commit()
                    logger.info(f"Updated song {title} by {artist} with ID {song_id}")
                    
                finally:
                    cursor.close()
                    
        except Exception as e:
            error_msg = f"Failed to update song: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)
            
    except Exception as e:
        error_msg = f"Failed to save song: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg)

def get_song_vocabulary(song_id: str) -> List[Dict[str, Any]]:
    """Get all vocabulary items for a specific song.
    
    Args:
        song_id: Unique identifier for the song
        
    Returns:
        List of vocabulary items with word and context
        
    Raises:
        StorageError: If retrieval fails
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                # First get the song details
                cursor.execute(
                    "SELECT title, artist FROM songs WHERE id = ?",
                    (song_id,)
                )
                song_row = cursor.fetchone()
                if not song_row:
                    raise StorageError(f"Song with ID {song_id} not found")
                    
                title, artist = song_row
                
                # Then get the vocabulary items
                cursor.execute(
                    "SELECT word, context FROM vocabulary WHERE song_title = ? AND artist = ?",
                    (title, artist)
                )
                items = [{
                    "word": row[0],
                    "context": row[1]
                } for row in cursor.fetchall()]
                
                return items
                
            finally:
                cursor.close()
                
    except Exception as e:
        error_msg = f"Failed to get vocabulary for song {song_id}: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg)
