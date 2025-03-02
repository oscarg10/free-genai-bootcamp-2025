import os
from typing import List, Dict, Any
import logging
import asyncio
from dotenv import load_dotenv
from serpapi import GoogleSearch
import aiohttp
from bs4 import BeautifulSoup
from src.exceptions import LyricsNotFoundError, LyricsError

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def clean_lyrics(html_content: str) -> str:
    """Clean and extract lyrics from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        if not cleaned_text or len(cleaned_text.strip()) < 10:
            raise LyricsError("Could not extract meaningful lyrics from content")
            
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error cleaning lyrics: {str(e)}")
        raise LyricsError(f"Error cleaning lyrics: {str(e)}")

async def search_lyrics(song_title: str, artist: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Search for lyrics using Google Search API via SerpApi with timeouts.
    
    Args:
        song_title (str): Title of the song
        artist (str): Name of the artist
        timeout (int): Timeout in seconds for the entire operation
        
    Returns:
        List[Dict[str, Any]]: List of search results with lyrics
        
    Raises:
        LyricsNotFoundError: If no lyrics are found
        LyricsError: If there's an error fetching lyrics
    """
    try:
        # For now, use mock data while we test the error handling
        mock_lyrics = f"""Yesterday all my troubles seemed so far away.
Now it looks as though they're here to stay.
Oh, I believe in yesterday.

Suddenly I'm not half the man I used to be.
There's a shadow hanging over me.
Oh, yesterday came suddenly.

Why she had to go, I don't know, she wouldn't say.
I said something wrong, now I long for yesterday.

Yesterday love was such an easy game to play.
Now I need a place to hide away.
Oh, I believe in yesterday."""

        # Simulate async operation
        await asyncio.sleep(0.5)
        
        # Simulate potential errors for testing
        if not song_title or not artist:
            raise LyricsError("Song title and artist are required")
            
        if song_title.lower() == "error":
            raise LyricsError("Simulated error for testing")
            
        if song_title.lower() == "timeout":
            await asyncio.sleep(timeout + 1)
            
        return [{
            'title': f"{song_title} by {artist}",
            'link': 'https://example.com',
            'body': mock_lyrics
        }]
        
        # Real implementation (commented out for now)
        '''
        async with aiohttp.ClientSession() as session:
            # Step 1: Search for lyrics pages
            try:
                query = f"{song_title} {artist} lyrics"
                search = GoogleSearch({
                    "q": query,
                    "api_key": os.getenv("SERPAPI_KEY"),
                    "num": 5
                })
                
                results = search.get_dict().get("organic_results", [])
                if not results:
                    raise LyricsNotFoundError(song_title, artist)
                    
                # Step 2: Try to get lyrics from results
                for result in results:
                    try:
                        async with session.get(
                            result['link'],
                            headers={'User-Agent': 'Mozilla/5.0'},
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            response.raise_for_status()
                            content = await response.text()
                            
                            lyrics = await clean_lyrics(content)
                            return [{
                                'title': result.get('title', f"{song_title} by {artist}"),
                                'link': result['link'],
                                'body': lyrics
                            }]
                            
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout fetching from {result['link']}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error fetching from {result['link']}: {str(e)}")
                        continue
                        
                raise LyricsError("Could not extract lyrics from any source")
                
            except asyncio.TimeoutError:
                raise LyricsError(
                    message=f"Lyrics search timed out after {timeout} seconds",
                    error_code='LYRICS_TIMEOUT'
                )
        '''
        
    except asyncio.TimeoutError:
        logger.error(f"Lyrics search timed out for {song_title} by {artist}")
        raise LyricsError(
            message=f"Lyrics search timed out after {timeout} seconds",
            error_code='LYRICS_TIMEOUT'
        )
    except LyricsError:
        # Re-raise lyrics-specific errors
        raise
    except Exception as e:
        logger.error(f"Error searching lyrics: {str(e)}")
        raise LyricsError(f"Error searching lyrics: {str(e)}")
