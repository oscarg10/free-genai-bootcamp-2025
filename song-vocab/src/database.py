import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from exceptions import StorageError

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
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")
                
                # Drop existing tables in reverse order to handle foreign keys
                cursor.execute("DROP TABLE IF EXISTS vocabulary")
                cursor.execute("DROP TABLE IF EXISTS songs")
                cursor.execute("DROP TABLE IF EXISTS study_sessions")
                
                # Create study sessions table first (no foreign keys)
                cursor.execute("""
                    CREATE TABLE study_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER NOT NULL,
                        study_activity_id INTEGER NOT NULL,
                        external_session_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create songs table second (no foreign keys)
                cursor.execute("""
                    CREATE TABLE songs (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        artist TEXT NOT NULL,
                        lyrics TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create vocabulary table last (has foreign keys)
                cursor.execute("""
                    CREATE TABLE vocabulary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        song_id TEXT,
                        word TEXT NOT NULL,
                        song_title TEXT NOT NULL,
                        artist TEXT NOT NULL,
                        context TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES study_sessions(id),
                        FOREIGN KEY (song_id) REFERENCES songs(id)
                    )
                """)
                
                # Create indices for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_vocabulary_session ON vocabulary(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_vocabulary_song ON vocabulary(song_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_group ON study_sessions(group_id)')
                
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
        raise StorageError(error_msg)

def save_vocabulary_items(items: List[Dict[str, str]], song_id: str, song_title: str, artist: str, session_id: Optional[int] = None) -> None:
    """Save multiple vocabulary items for a song.
    
    Args:
        items: List of vocabulary items with word and context
        song_id: Unique identifier for the song
        song_title: Title of the song
        artist: Name of the artist
        session_id: Optional ID of the study session
        
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
                        """INSERT INTO vocabulary 
                           (word, song_title, artist, context, song_id, session_id) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (item["word"], song_title, artist, item["context"], song_id, session_id)
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

def create_study_session(group_id: int) -> int:
    """Create a new study session for a group.
    
    Args:
        group_id: ID of the group starting the session
        
    Returns:
        ID of the created session
        
    Raises:
        StorageError: If session creation fails
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO study_sessions (group_id, created_at) VALUES (?, ?)",
                    (group_id, datetime.utcnow().isoformat())
                )
                session_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Created study session {session_id} for group {group_id}")
                return session_id
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                
    except Exception as e:
        error_msg = f"Failed to create study session: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg)

def save_session_vocabulary(session_id: int, items: List[Dict[str, str]], song_title: str, artist: str) -> None:
    """Save vocabulary items for a specific study session.
    
    Args:
        session_id: ID of the study session
        items: List of vocabulary items with word and context
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
                
                # Insert vocabulary items with session_id
                for item in items:
                    cursor.execute(
                        "INSERT INTO vocabulary (session_id, word, song_title, artist, context) VALUES (?, ?, ?, ?, ?)",
                        (session_id, item["word"], song_title, artist, item["context"])
                    )
                
                conn.commit()
                logger.info(f"Saved {len(items)} vocabulary items for session {session_id}")
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
                
    except Exception as e:
        error_msg = f"Failed to save session vocabulary: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg)

def get_session_vocabulary(session_id: int) -> List[Dict[str, Any]]:
    """Get all vocabulary items for a specific study session.
    
    Args:
        session_id: ID of the study session
        
    Returns:
        List of vocabulary items with word, context, song title, and artist
        
    Raises:
        StorageError: If retrieval fails
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """SELECT word, context, song_title, artist 
                       FROM vocabulary 
                       WHERE session_id = ?
                    """,
                    (session_id,)
                )
                items = [{
                    "word": row[0],
                    "context": row[1],
                    "song_title": row[2],
                    "artist": row[3]
                } for row in cursor.fetchall()]
                
                return items
                
            finally:
                cursor.close()
                
    except Exception as e:
        error_msg = f"Failed to get session vocabulary: {str(e)}"
        logger.error(error_msg)
        raise StorageError(error_msg)
