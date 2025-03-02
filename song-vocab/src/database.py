import sqlite3
from pathlib import Path

def init_db():
    db_path = Path("vocab.db")
    with sqlite3.connect(db_path) as conn:
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
            conn.commit()
        finally:
            cursor.close()

def save_vocabulary(word: str, song_title: str, artist: str, context: str = None):
    with sqlite3.connect("vocab.db") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO vocabulary (word, song_title, artist, context) VALUES (?, ?, ?, ?)",
                (word, song_title, artist, context)
            )
            conn.commit()
        finally:
            cursor.close()
