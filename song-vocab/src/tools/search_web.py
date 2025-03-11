import os
from typing import List, Dict, Any
import logging
import asyncio
from dotenv import load_dotenv
from serpapi import GoogleSearch
import aiohttp
from bs4 import BeautifulSoup
import re

# Define exceptions
class LyricsError(Exception):
    """Base exception for lyrics-related errors"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class LyricsNotFoundError(LyricsError):
    """Exception raised when lyrics cannot be found"""
    pass

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def clean_lyrics(html_content: str) -> str:
    """Clean and extract lyrics from HTML content."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'head', 'header', 'footer', 'nav']):
            element.decompose()
            
        # Common lyrics container classes and IDs
        lyrics_selectors = [
            '.lyrics',  # Common class for lyrics
            '#lyrics',  # Common ID for lyrics
            '.lyric-content',
            '.songtext',
            '#songtext',
            '.text-lyrics',
            'div[class*="lyrics"]',  # Any div with 'lyrics' in class
            'div[class*="songtext"]'  # Any div with 'songtext' in class
        ]
        
        # Try to find lyrics container
        lyrics_element = None
        for selector in lyrics_selectors:
            lyrics_element = soup.select_one(selector)
            if lyrics_element:
                break
                
        if not lyrics_element:
            # Fallback: Look for the largest text block
            text_blocks = soup.find_all(['div', 'p'])
            if text_blocks:
                lyrics_element = max(text_blocks, key=lambda x: len(x.get_text()))
        
        if lyrics_element:
            # Get text and clean it
            lyrics = lyrics_element.get_text()
            
            # Clean up the text
            lyrics = re.sub(r'\[.*?\]', '', lyrics)  # Remove [Verse], [Chorus] etc.
            lyrics = re.sub(r'\{.*?\}', '', lyrics)  # Remove any {...} tags
            lyrics = re.sub(r'<!--.*?-->', '', lyrics)  # Remove HTML comments
            lyrics = re.sub(r'\s*\n\s*\n\s*', '\n\n', lyrics)  # Normalize line breaks
            lyrics = re.sub(r'^\s+|\s+$', '', lyrics, flags=re.MULTILINE)  # Trim lines
            
            return lyrics.strip()
            
        return ""
        
    except Exception as e:
        logger.error(f"Error cleaning lyrics: {str(e)}")
        raise LyricsError(f"Error cleaning lyrics: {str(e)}")

async def search_lyrics(song_title: str, artist: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """Search for lyrics using Google Search API via SerpApi with timeouts."""
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Search for lyrics pages using SerpAPI
            query = f"{song_title} {artist} songtext lyrics deutsch"
            search = GoogleSearch({
                "q": query,
                "api_key": os.getenv("SERPAPI_KEY"),
                "num": 5,
                "hl": "de",  # Set language to German
                "gl": "de",  # Set region to Germany
            })
            
            search_results = search.get_dict().get("organic_results", [])
            
            if not search_results:
                raise LyricsNotFoundError(f"No lyrics found for {song_title} by {artist}")
            
            # Step 2: Process each search result
            results = []
            for result in search_results:
                try:
                    if 'link' not in result:
                        continue
                        
                    # Fetch and clean the lyrics with proper encoding
                    async with session.get(result['link'], timeout=timeout) as response:
                        if response.status != 200:
                            continue
                            
                        # Try to get the correct encoding from the response headers
                        content_type = response.headers.get('content-type', '')
                        encoding = 'utf-8'  # default encoding
                        if 'charset=' in content_type:
                            encoding = content_type.split('charset=')[-1]
                            
                        try:
                            html = await response.text(encoding=encoding)
                        except UnicodeDecodeError:
                            # If that fails, try with different common encodings
                            for enc in ['iso-8859-1', 'cp1252', 'latin1']:
                                try:
                                    html = await response.text(encoding=enc)
                                    break
                                except UnicodeDecodeError:
                                    continue
                        
                        lyrics = await clean_lyrics(html)
                        
                        if lyrics:
                            results.append({
                                'title': result.get('title', ''),
                                'link': result['link'],
                                'lyrics': lyrics
                            })
                            
                except Exception as e:
                    logger.error(f"Error processing result: {str(e)}")
                    continue
                    
            if not results:
                raise LyricsNotFoundError(f"Could not extract lyrics for {song_title} by {artist}")
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching for lyrics: {str(e)}")
            raise LyricsError(f"Error searching for lyrics: {str(e)}")

async def test_search():
    """Test function to demonstrate lyrics search"""
    # Configure logging
    logging.basicConfig(level=logging.ERROR)  # Only show errors
    
    title = "99 Luftballons"
    artist = "Nena"
    
    try:
        results = await search_lyrics(title, artist)
        
        # Return only the first result that has German lyrics
        if results:
            result = results[0]
            return {
                'title': title,
                'artist': artist,
                'url': result['link'],
                'lyrics': result['lyrics']
            }
        
    except Exception as e:
        logger.error(str(e))
        return None

async def test_pipeline():
    """Test the complete lyrics search and vocabulary extraction pipeline"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    from database import init_db
    init_db()
    
    # Test song
    title = "99 Luftballons"
    artist = "Nena"
    
    try:
        logger.info(f"Testing pipeline with: {title} by {artist}")
        
        # Step 1: Search for lyrics
        logger.info("1. Searching for lyrics...")
        search_result = await test_search()
        if not search_result:
            logger.error("Could not find lyrics")
            return
        logger.info(f"Found lyrics with length: {len(search_result['lyrics'])}")
            
        # Step 2: Generate song ID
        logger.info("2. Generating song ID...")
        from src.tools.generate_song_id import generate_song_id
        song_id = generate_song_id(title, artist)
        logger.info(f"Generated song_id: {song_id}")
        
        # Step 3: Extract vocabulary
        logger.info("3. Extracting vocabulary...")
        from src.tools.extract_vocabulary import extract_vocabulary
        logger.info("Calling extract_vocabulary with 60s timeout...")
        vocabulary = await extract_vocabulary(search_result['lyrics'], timeout=60)  # Increase timeout to 60 seconds
        logger.info(f"Extracted {len(vocabulary)} vocabulary items")
        
        # Step 4: Save results
        logger.info("4. Saving results...")
        from src.tools.save_results import save_results
        logger.info("Calling save_results...")
        result = save_results(
            song_id=song_id,
            lyrics=search_result['lyrics'],
            vocabulary=vocabulary,
            title=title,
            artist=artist
        )
        
        logger.info(f"FINISHED! Results saved with song_id: {song_id}")
        logger.info(f"- Lyrics: outputs/lyrics/{song_id}.txt")
        logger.info(f"- Vocabulary: outputs/vocabulary/{song_id}.json")
        
    except Exception as e:
        logger.error(f"Pipeline Error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Add project root to Python path
    import os
    import sys
    from pathlib import Path
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    
    # Add to Python path
    sys.path.insert(0, str(project_root))
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run the pipeline test
    asyncio.run(test_pipeline())
