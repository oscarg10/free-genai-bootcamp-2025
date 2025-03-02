from typing import List, Dict, Any
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger('song_vocab')

def save_results(song_id: str, lyrics: str, vocabulary: List[Any], title: str, artist: str) -> Dict[str, Any]:
    """
    Save lyrics and vocabulary to the database and return a summary.
    
    Args:
        song_id (str): ID of the song
        lyrics (str): Song lyrics text
        vocabulary (List[Any]): List of vocabulary items (VocabularyItem or Dict)
        title (str): Song title
        artist (str): Artist name
    
    Returns:
        Dict[str, Any]: Summary of saved data
    """
    # Create data directories if they don't exist
    data_dir = Path(os.getenv('DATA_DIR', 'data'))
    lyrics_dir = data_dir / 'lyrics'
    vocab_dir = data_dir / 'vocabulary'
    
    for directory in [data_dir, lyrics_dir, vocab_dir]:
        directory.mkdir(exist_ok=True)
    
    # Save lyrics
    lyrics_file = lyrics_dir / f"{song_id}.txt"
    lyrics_file.write_text(lyrics)
    logger.info(f"Saved lyrics to {lyrics_file}")
    
    # Convert vocabulary items to dict format
    vocab_list = []
    for item in vocabulary:
        if hasattr(item, 'dict'):
            # Handle Pydantic models
            vocab_list.append(item.dict())
        elif isinstance(item, dict):
            # Handle dictionaries
            vocab_list.append(item)
        else:
            # Handle other types by getting word and context attributes
            vocab_list.append({
                'word': getattr(item, 'word', str(item)),
                'context': getattr(item, 'context', '')
            })
    
    # Save vocabulary with metadata
    vocab_data = {
        'song_id': song_id,
        'title': title,
        'artist': artist,
        'vocabulary': vocab_list,
        'total_words': len(vocab_list)
    }
    
    vocab_file = vocab_dir / f"{song_id}.json"
    vocab_file.write_text(json.dumps(vocab_data, ensure_ascii=False, indent=2))
    logger.info(f"Saved vocabulary to {vocab_file}")
    
    return {
        'song_id': song_id,
        'title': title,
        'artist': artist,
        'lyrics_file': str(lyrics_file),
        'vocabulary_file': str(vocab_file),
        'total_words': len(vocabulary)
    }