import hashlib
import re
from datetime import datetime
from typing import Dict

def generate_song_id(artist: str, title: str) -> Dict[str, str]:
    """
    Generate a unique song ID based on title and artist.
    Format: YYYYMMDD-<first 8 chars of hash>
    
    Args:
        artist (str): The artist name
        title (str): The song title
        
    Returns:
        Dict[str, str]: Dictionary containing the generated song_id
    """
    # Clean the input strings
    title = re.sub(r'[^\w\s]', '', title.lower())
    artist = re.sub(r'[^\w\s]', '', artist.lower())
    
    # Create a string to hash
    to_hash = f"{title}-{artist}"
    
    # Generate hash
    hash_obj = hashlib.sha256(to_hash.encode())
    hash_str = hash_obj.hexdigest()[:8]
    
    # Get current date
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Combine date and hash
    song_id = f"{date_str}-{hash_str}"
    return {"song_id": song_id}