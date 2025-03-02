from typing import List, Dict, Any
import logging
from src.tools.search_web import search_lyrics
from src.tools.extract_vocabulary import extract_vocabulary, VocabularyItem
from src.tools.generate_song_id import generate_song_id
from src.tools.save_results import save_results
from src.exceptions import LyricsError, LyricsNotFoundError, VocabularyError, StorageError

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self):
        self.thought_history = []
    
    def _add_thought(self, thought: str):
        """Record agent's thought process"""
        self.thought_history.append(thought)
        print(f"Thought: {thought}")  # For debugging
    
    def _parse_song_request(self, message: str) -> tuple[str, str]:
        """Parse song title and artist from the request"""
        self._add_thought(f"Parsing request: {message}")
        
        # Try 'by' format first
        if ' by ' in message:
            title, artist = message.split(' by ', 1)
            self._add_thought(f"Found explicit 'by' format. Title: {title}, Artist: {artist}")
            return title.strip(), artist.strip()
        
        # Try to extract from space-separated string
        words = message.split()
        if len(words) > 2:
            # Assume last two words are artist name
            artist = ' '.join(words[-2:])
            title = ' '.join(words[:-2])
            self._add_thought(f"Extracted from words. Title: {title}, Artist: {artist}")
            return title.strip(), artist.strip()
        
        # Fallback: treat entire input as title
        self._add_thought(f"Using entire input as title: {message}")
        return message.strip(), ""

    async def process_request(self, message: str) -> Dict[str, Any]:
        """
        Process a song request using the reAct framework:
        1. Parse request
        2. Search for lyrics
        3. Extract vocabulary
        4. Save results
        5. Return response
        """
        try:
            # Step 1: Parse request
            if not message or not message.strip():
                raise LyricsError("Empty request message")
                
            song_title, artist = self._parse_song_request(message)
            if not song_title:
                raise LyricsError("Could not parse song title from request")
                
            self._add_thought(f"Looking for lyrics of '{song_title}' by '{artist}'")
            
            # Step 2: Search for lyrics with timeout
            try:
                search_results = await search_lyrics(song_title, artist, timeout=10)
                lyrics = search_results[0].get('body', '')
                if not lyrics:
                    raise LyricsError("Empty lyrics returned from search")
                    
                self._add_thought("Successfully found lyrics, extracting vocabulary")
                
            except (LyricsNotFoundError, LyricsError) as e:
                self._add_thought(f"Lyrics error: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e)
                }
            
            # Step 3: Extract vocabulary with timeout
            try:
                vocab_items = await extract_vocabulary(lyrics, timeout=5)
                if not vocab_items:
                    raise VocabularyError("No vocabulary items extracted")
                    
                self._add_thought(f"Extracted {len(vocab_items)} vocabulary items")
                
            except VocabularyError as e:
                self._add_thought(f"Vocabulary error: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e),
                    "lyrics": lyrics
                }
            
            # Step 4: Generate song ID and save results
            try:
                song_id_result = generate_song_id(artist, song_title)
                song_id = song_id_result["song_id"]
                
                save_result = save_results(
                    song_id=song_id,
                    lyrics=lyrics,
                    vocabulary=vocab_items,
                    title=song_title,
                    artist=artist
                )
                
                self._add_thought(f"Saved results with ID: {song_id}")
                
            except StorageError as e:
                self._add_thought(f"Storage error: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e),
                    "lyrics": lyrics,
                    "vocabulary": [item.dict() for item in vocab_items]
                }
            
            # Step 5: Return response
            # Convert VocabularyItems to dicts for JSON serialization
            vocab_dicts = []
            for item in vocab_items:
                if isinstance(item, VocabularyItem):
                    vocab_dicts.append({"word": item.word, "context": item.context})
                else:
                    vocab_dicts.append(item)
                    
            return {
                "status": "success",
                "song_id": song_id,
                "title": song_title,
                "artist": artist,
                "lyrics": lyrics,
                "vocabulary": vocab_dicts,
                "files": {
                    "lyrics": save_result["lyrics_file"],
                    "vocabulary": save_result["vocabulary_file"]
                },
                "total_words": save_result["total_words"]
            }
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self._add_thought(f"Unexpected error: {str(e)}")
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }

    def get_thought_history(self) -> List[str]:
        """Get the agent's thought process history"""
        return self.thought_history
