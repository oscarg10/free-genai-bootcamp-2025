from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime
import sqlite3
import uuid

from agent import Agent
from database import init_db
from exceptions import LyricsError, LyricsNotFoundError, VocabularyError, StorageError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Song Vocabulary Extractor")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent()

class LyricsRequest(BaseModel):
    song_title: str
    artist: str
    session_id: Optional[int] = None
    study_activity_id: Optional[int] = None
    external_session_id: Optional[int] = None

class VocabularyItem(BaseModel):
    word: str
    context: str
    
    @classmethod
    def from_dict(cls, item_dict: Dict[str, str]) -> 'VocabularyItem':
        return cls(word=item_dict['word'], context=item_dict['context'])
    
    def dict(self) -> Dict[str, str]:
        return {'word': self.word, 'context': self.context}

class LyricsResponse(BaseModel):
    status: str
    error: Optional[str] = None
    song_id: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    lyrics: Optional[str] = None
    vocabulary: Optional[List[VocabularyItem]] = None
    files: Optional[Dict[str, str]] = None
    total_words: Optional[int] = None

class ThoughtResponse(BaseModel):
    thoughts: List[str]

@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")

@app.post("/api/agent", response_model=LyricsResponse)
async def get_lyrics(request: LyricsRequest):
    try:
        # Initialize agent
        agent = Agent()
        
        # Get lyrics and vocabulary
        lyrics = await agent.get_lyrics(request.song_title, request.artist)
        vocabulary = await agent.get_vocabulary(lyrics)
        
        # Generate song ID
        song_id = str(uuid.uuid4())
        
        # Save results with proper transaction handling
        with sqlite3.connect('data/vocab.db') as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                cursor = conn.cursor()
                
                try:
                    # Create study session if needed
                    session_id = None
                    if request.study_activity_id:
                        cursor.execute(
                            """INSERT INTO study_sessions 
                               (group_id, study_activity_id, external_session_id)
                               VALUES (?, ?, ?)""",
                            (1, request.study_activity_id, request.external_session_id)
                        )
                        session_id = cursor.lastrowid
                    
                    # Save song
                    cursor.execute(
                        "INSERT INTO songs (id, title, artist, lyrics) VALUES (?, ?, ?, ?)",
                        (song_id, request.song_title, request.artist, lyrics)
                    )
                    
                    # Save vocabulary items
                    for item in vocabulary:
                        cursor.execute(
                            """INSERT INTO vocabulary 
                               (word, context, song_id, song_title, artist, session_id)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (item.word, item.context, song_id, request.song_title, 
                             request.artist, session_id or request.session_id)
                        )
                    
                    conn.commit()
                    
                    # Convert VocabularyItems to dicts for response
                    vocab_dicts = [item.dict() for item in vocabulary]
                    
                    return LyricsResponse(
                        status="success",
                        song_id=song_id,
                        title=request.song_title,
                        artist=request.artist,
                        lyrics=lyrics,
                        vocabulary=vocab_dicts,
                        total_words=len(vocabulary)
                    )
                    
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    cursor.close()
                    
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
    except LyricsNotFoundError as e:
        logger.error(f"Lyrics not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except LyricsError as e:
        logger.error(f"Lyrics error: {str(e)}")
        status_code = 408 if "timeout" in str(e).lower() else 500
        raise HTTPException(status_code=status_code, detail=str(e))
        
    except VocabularyError as e:
        logger.error(f"Vocabulary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except StorageError as e:
        logger.error(f"Storage error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.get("/api/thoughts", response_model=ThoughtResponse)
async def get_agent_thoughts():
    """Get the agent's thought process history"""
    try:
        thoughts = agent.get_thought_history()
        return ThoughtResponse(thoughts=thoughts)
        
    except Exception as e:
        logger.error(f"Error getting thought history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving thought history: {str(e)}"
        )

# Database connection helper
def get_db():
    try:
        conn = sqlite3.connect('vocabulary.db')
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/sessions")
async def create_session(group_id: int):
    try:
        with sqlite3.connect('data/vocab.db') as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute(
                    "INSERT INTO study_sessions (group_id, created_at) VALUES (?, ?)",
                    (group_id, datetime.utcnow().isoformat())
                )
                session_id = cursor.lastrowid
                conn.commit()
                return {"session_id": session_id}
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/vocabulary")
async def get_session_vocabulary(session_id: int):
    try:
        with sqlite3.connect('data/vocab.db') as conn:
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT word, context, song_title, artist 
                    FROM vocabulary 
                    WHERE session_id = ?
                """, (session_id,))
                vocab = cursor.fetchall()
                return {
                    "vocabulary": [
                        {
                            "word": row["word"],
                            "context": row["context"],
                            "song_title": row["song_title"],
                            "artist": row["artist"]
                        } for row in vocab
                    ]
                }
            finally:
                cursor.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
