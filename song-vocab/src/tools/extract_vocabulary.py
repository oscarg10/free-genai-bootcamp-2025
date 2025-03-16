from typing import List, Dict, Any, Optional
import json
import asyncio
import httpx
from pydantic import BaseModel
import logging
from ollama import AsyncClient
from exceptions import VocabularyError

# Ollama configuration
OLLAMA_HOST = 'http://localhost:11434'
OLLAMA_MODEL = 'mistral:latest'  # Include the tag

logger = logging.getLogger(__name__)

class VocabularyItem(BaseModel):
    """A vocabulary item with its context"""
    word: str
    context: str
    
    def dict(self) -> Dict[str, str]:
        """Convert to dictionary format"""
        return {
            "word": self.word,
            "context": self.context
        }

async def mock_vocabulary(lyrics: str) -> List[Dict[str, str]]:
    """Generate mock vocabulary items for testing
    
    Args:
        lyrics (str): Song lyrics to analyze
        
    Returns:
        List[Dict[str, str]]: List of mock vocabulary items
        
    Raises:
        VocabularyError: If lyrics are empty or invalid
    """
    if not lyrics or not lyrics.strip():
        raise VocabularyError("Cannot extract vocabulary from empty lyrics")
        
    # Simulate async processing
    await asyncio.sleep(0.5)
    
    # Extract some words from the lyrics for realistic mock data
    words = [word for word in lyrics.split() if len(word) > 3][:5]  # Take first 5 words longer than 3 chars
    
    if not words:
        raise VocabularyError("No suitable words found in lyrics")
    
    return [
        {
            "word": word,
            "context": f"Found in lyrics: '{word}'"
        } for word in words
    ]

async def check_ollama() -> bool:
    """Check if Ollama is running and responsive"""
    try:
        logger.info("Checking Ollama status...")
        # Try to list models using AsyncClient
        client = AsyncClient(host=OLLAMA_HOST)
        models = await client.list()
        logger.info(f"Found models: {[m['name'] for m in models['models']]}")
        
        # Check if our model is available
        available_models = [m['name'] for m in models['models']]
        logger.info(f"Available models: {available_models}")
        if OLLAMA_MODEL not in available_models:
            logger.error(f"Model {OLLAMA_MODEL} not found. Please run 'ollama pull {OLLAMA_MODEL}'")
            return False
            
        logger.info(f"Found required model: {OLLAMA_MODEL}")
        return True
    except Exception as e:
        logger.error(f"Ollama check failed: {str(e)}")
        return False

async def extract_vocabulary(lyrics: str, timeout: int = 30) -> List[VocabularyItem]:
    """
    Extract vocabulary items from lyrics using mock data for testing.
    
    Args:
        lyrics (str): Song lyrics to analyze
        timeout (int): Timeout in seconds
        
    Returns:
        List[VocabularyItem]: List of vocabulary items
        
    Raises:
        VocabularyError: If extraction fails or times out
    """
    try:
        # Use mock vocabulary for testing
        mock_items = await mock_vocabulary(lyrics)
        
        # Convert mock items to VocabularyItems
        result = [VocabularyItem(**item) for item in mock_items]
        
        if not result:
            raise VocabularyError("No valid vocabulary items found")
        
        return result
        
        # Real implementation (commented out for now)
        '''
        prompt = f"""
        Analyze these lyrics and identify 5 important vocabulary words.
        Return the response in this exact JSON format:
        [{{
            "word": "example_word",
            "context": "line where the word appears"
        }}]
        
        Lyrics:
        {lyrics}
        
        Focus on words that are:
        - Important for understanding the song
        - Potentially new or challenging
        - Used in interesting or poetic ways
        """
        
        # Create a task for ollama chat
        async def run_ollama():
            try:
                response = await ollama.chat(model='mistral', messages=[{
                    'role': 'user',
                    'content': prompt
                }])
                return response
            except Exception as e:
                raise VocabularyError(
                    message=f"Error from Ollama API: {str(e)}",
                    error_code="OLLAMA_ERROR"
                )
        
        # Run with timeout
        try:
            response = await asyncio.wait_for(run_ollama(), timeout=timeout)
        except asyncio.TimeoutError:
            raise VocabularyError(
                message=f"Vocabulary extraction timed out after {timeout} seconds",
                error_code="VOCAB_TIMEOUT"
            )
        
        # Parse response
        try:
            response_text = response['message']['content']
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            
            if start == -1 or end <= 0:
                raise VocabularyError(
                    message="Could not find JSON array in response",
                    error_code="PARSE_ERROR"
                )
            
            json_str = response_text[start:end]
            vocab_items = json.loads(json_str)
            
            # Validate items
            if not vocab_items:
                raise VocabularyError(
                    message="No vocabulary items found in response",
                    error_code="NO_ITEMS"
                )
                
            return [VocabularyItem(**item) for item in vocab_items]
            
        except json.JSONDecodeError as e:
            raise VocabularyError(
                message=f"Invalid JSON in response: {str(e)}",
                error_code="JSON_ERROR"
            )
        except Exception as e:
            raise VocabularyError(
                message=f"Error parsing response: {str(e)}",
                error_code="PARSE_ERROR"
            )
        '''
        
    except VocabularyError:
        # Re-raise vocabulary-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error in vocabulary extraction: {str(e)}")
        raise VocabularyError(
            message=f"Unexpected error in vocabulary extraction: {str(e)}",
            error_code="UNEXPECTED"
        )
