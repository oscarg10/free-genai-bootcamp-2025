from typing import List, Dict, Any, Optional
import json
import asyncio
import httpx
from pydantic import BaseModel
import logging
from ollama import AsyncClient
from src.exceptions import VocabularyError

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
    Extract vocabulary items from lyrics using Ollama with timeout.
    
    Args:
        lyrics (str): Song lyrics to analyze
        timeout (int): Timeout in seconds
        
    Returns:
        List[VocabularyItem]: List of vocabulary items
        
    Raises:
        VocabularyError: If extraction fails or times out
    """
    try:
        # First check if Ollama is running
        if not await check_ollama():
            raise VocabularyError(
                "Ollama is not running or not responding. Please start Ollama with 'ollama serve' and try again."
            )
        
        logger.info(f"Starting vocabulary extraction with timeout={timeout}s")
        logger.debug(f"Lyrics length: {len(lyrics)} characters")
        
        # Input validation
        if not lyrics or not lyrics.strip():
            raise VocabularyError("Cannot extract vocabulary from empty lyrics")
        
        logger.info("Input validation passed")
            
        # Prepare the prompt for Ollama
        prompt = f"""
        Extract 5 important German vocabulary words from these lyrics.
        Format as a JSON array with 'word' and 'context' fields.
        Only return the JSON array, nothing else.
        
        Example format:
        [
            {{
                "word": "Luftballons",
                "context": "99 Luftballons auf ihrem Weg zum Horizont"
            }}
        ]
        
        Lyrics:
        {lyrics}
        """
        
        try:
            logger.info("Calling Ollama API...")
            # Create a new client for this request
            client = AsyncClient(host=OLLAMA_HOST)
            # Use streaming to get response chunks
            full_response = ""
            async for chunk in await client.generate(
                model=OLLAMA_MODEL,
                prompt=prompt,
                stream=True,  # Enable streaming
                options={
                    "temperature": 0.1,
                    "top_k": 10,
                    "top_p": 0.9,
                    "num_predict": 200
                }
            ):
                if chunk and 'response' in chunk:
                    full_response += chunk['response']
                    
            # Use the full response
            response = {'response': full_response}
            
            # Parse the response
            try:
                # For streaming, we already have the raw response
                json_str = full_response.strip()
                logger.debug(f"Raw response: {json_str}")
                
                # Try to find JSON array in the response
                start_idx = json_str.find('[')
                end_idx = json_str.rfind(']') + 1
                
                if start_idx == -1 or end_idx == 0:
                    raise VocabularyError("Could not find JSON array in response")
                    
                json_str = json_str[start_idx:end_idx]
                
                # Parse JSON
                items = json.loads(json_str)
                if not isinstance(items, list):
                    raise VocabularyError("Invalid response format from Ollama")
                    
                # Validate and create VocabularyItems
                result = []
                for item in items:
                    if not isinstance(item, dict) or 'word' not in item or 'context' not in item:
                        logger.warning(f"Skipping invalid vocabulary item: {item}")
                        continue
                    result.append(VocabularyItem(**item))
                
                if not result:
                    raise VocabularyError("No valid vocabulary items found in response")
                    
                return result
                
            except json.JSONDecodeError as e:
                raise VocabularyError(f"Failed to parse Ollama response: {str(e)}")
                
        except asyncio.TimeoutError:
            raise VocabularyError(
                message=f"Vocabulary extraction timed out after {timeout} seconds",
                error_code="VOCAB_TIMEOUT"
            )
        
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
