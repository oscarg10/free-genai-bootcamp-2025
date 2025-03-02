from typing import List, Dict, Any, Optional
import json
import asyncio
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class VocabularyItem(BaseModel):
    word: str
    context: str

class VocabularyError(Exception):
    """Base class for vocabulary extraction errors"""
    pass

class TimeoutError(VocabularyError):
    """Raised when vocabulary extraction times out"""
    pass

class ParseError(VocabularyError):
    """Raised when response parsing fails"""
    pass

def mock_vocabulary(lyrics: str) -> List[Dict[str, str]]:
    """Generate mock vocabulary items for testing"""
    # Extract some words from the lyrics for realistic mock data
    words = lyrics.split()[:5]  # Take first 5 words
    return [
        {
            "word": word,
            "context": f"Found in lyrics: '{word}'"
        } for word in words
    ]

async def extract_vocabulary(lyrics: str, timeout: int = 5) -> List[VocabularyItem]:
    """
    Extract vocabulary items from lyrics with timeout.
    
    Args:
        lyrics (str): Song lyrics to analyze
        timeout (int): Timeout in seconds
        
    Returns:
        List[VocabularyItem]: List of vocabulary items
        
    Raises:
        TimeoutError: If extraction takes too long
        ParseError: If response parsing fails
    """
    try:
        # For now, use mock data to test the flow
        # This ensures quick responses while we fix the infrastructure
        mock_items = mock_vocabulary(lyrics)
        return [VocabularyItem(**item) for item in mock_items]
        
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
            response = await ollama.chat(model='mistral', messages=[{
                'role': 'user',
                'content': prompt
            }])
            return response
        
        # Run with timeout
        try:
            response = await asyncio.wait_for(run_ollama(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Vocabulary extraction timed out after {timeout} seconds")
        
        # Parse response
        response_text = response['message']['content']
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        
        if start == -1 or end <= 0:
            raise ParseError("Could not find JSON array in response")
        
        json_str = response_text[start:end]
        vocab_items = json.loads(json_str)
        return [VocabularyItem(**item) for item in vocab_items]
        '''
        
    except VocabularyError:
        # Re-raise vocabulary-specific errors
        raise
    except Exception as e:
        logger.error(f"Error extracting vocabulary: {str(e)}")
        return []
