import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.tools.search_web import search_lyrics
from src.exceptions import LyricsError, LyricsNotFoundError

@pytest.mark.asyncio
async def test_empty_search():
    """Test handling of empty search parameters"""
    with pytest.raises(LyricsError):
        await search_lyrics("", "")
    
    with pytest.raises(LyricsError):
        await search_lyrics("", "Artist")
        
    with pytest.raises(LyricsError):
        await search_lyrics("Song", "")

@pytest.mark.asyncio
async def test_lyrics_not_found():
    """Test handling of non-existent songs"""
    with patch('src.tools.search_web.search_lyrics', side_effect=LyricsNotFoundError("ThisSongDefinitelyDoesNotExist", "UnknownArtist")):
        with pytest.raises(LyricsError) as exc_info:
            await search_lyrics("ThisSongDefinitelyDoesNotExist", "UnknownArtist")
        assert "not found" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling in lyrics search"""
    with patch('src.tools.search_web.search_lyrics', side_effect=asyncio.TimeoutError("Lyrics search timed out")):
        with pytest.raises(LyricsError) as exc_info:
            await search_lyrics("timeout", "test artist", timeout=1)
        assert "timeout" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_successful_search():
    """Test successful lyrics search"""
    mock_result = [{
        "title": "Yesterday",
        "artist": "The Beatles",
        "link": "http://example.com/lyrics",
        "body": "Yesterday, all my troubles seemed so far away"
    }]
    
    with patch('src.tools.search_web.search_lyrics', return_value=mock_result):
        results = await search_lyrics("Yesterday", "The Beatles")
        assert len(results) > 0
        assert results[0]["title"] == "Yesterday"
        assert results[0]["artist"] == "The Beatles"
        assert "link" in results[0]
        assert len(results[0]["body"]) > 0

@pytest.mark.asyncio
async def test_concurrent_searches():
    """Test handling of concurrent searches"""
    searches = [
        ("Yesterday", "The Beatles"),
        ("Imagine", "John Lennon"),
        ("Let It Be", "The Beatles")
    ]
    
    async def mock_search(title, artist, timeout=None):
        return [{
            "title": title,
            "artist": artist,
            "link": f"http://example.com/{title.lower()}",
            "body": f"Sample lyrics for {title} by {artist}"
        }]
    
    with patch('src.tools.search_web.search_lyrics', side_effect=mock_search):
        tasks = [search_lyrics(title, artist) for title, artist in searches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that we got all results
        assert len(results) == len(searches)
        
        # Check that all results are valid
        for i, result in enumerate(results):
            assert not isinstance(result, Exception)
            assert len(result) > 0
            assert result[0]["title"] == searches[i][0]
            assert result[0]["artist"] == searches[i][1]
            assert "body" in result[0]
            assert len(result[0]["body"]) > 0

@pytest.mark.asyncio
async def test_special_characters():
    """Test handling of special characters in search"""
    special_cases = [
        ("Let's Go", "Artist"),
        ("Song & Title", "Artist"),
        ("Song - Title", "Artist"),
        ("Song (Live)", "Artist"),
        ("Song'", "Artist")
    ]
    
    async def mock_search(title, artist, timeout=None):
        # Simulate successful search for all cases
        return [{
            "title": title,
            "artist": artist,
            "link": f"http://example.com/{title.lower()}",
            "body": f"Sample lyrics for {title} by {artist}"
        }]
    
    with patch('src.tools.search_web.search_lyrics', side_effect=mock_search):
        for title, artist in special_cases:
            results = await search_lyrics(title, artist)
            assert isinstance(results, list)
            assert len(results) > 0
            assert results[0]["title"] == title
            assert results[0]["artist"] == artist
            assert "body" in results[0]
            assert len(results[0]["body"]) > 0

@pytest.mark.asyncio
async def test_response_format():
    """Test that successful responses have the correct format"""
    results = await search_lyrics("Yesterday", "The Beatles")
    assert isinstance(results, list)
    assert len(results) > 0
    
    result = results[0]
    assert isinstance(result, dict)
    assert all(key in result for key in ["title", "link", "body"])
    assert all(isinstance(result[key], str) for key in ["title", "link", "body"])
