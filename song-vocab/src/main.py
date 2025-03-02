from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from src.agent import Agent
from src.database import init_db
from src.exceptions import LyricsError, LyricsNotFoundError, VocabularyError, StorageError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Song Vocabulary Extractor")
agent = Agent()

class LyricsRequest(BaseModel):
    message_request: str

class VocabularyItem(BaseModel):
    word: str
    context: str

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
        if not request.message_request or not request.message_request.strip():
            raise HTTPException(
                status_code=400,
                detail="Message request cannot be empty"
            )
        
        logger.info(f"Processing request: {request.message_request}")
        result = await agent.process_request(request.message_request)
        
        if result["status"] == "error":
            error_msg = result["error"]
            status_code = 500  # Default to internal server error
            
            # Map specific errors to appropriate HTTP status codes
            if "not found" in error_msg.lower():
                status_code = 404
            elif "timeout" in error_msg.lower():
                status_code = 408
            elif any(msg in error_msg.lower() for msg in ["empty", "invalid", "could not parse"]):
                status_code = 400
                
            logger.error(f"Error processing request: {error_msg}")
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": error_msg,
                    "lyrics": result.get("lyrics"),
                    "vocabulary": result.get("vocabulary", [])
                }
            )
        
        logger.info(f"Successfully processed request for song: {result['title']}")
        return LyricsResponse(**result)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
