import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from src.agent import Agent
from src.tools.extract_vocabulary import client as ollama_client
from src.exceptions import LyricsError, LyricsNotFoundError, VocabularyError, StorageError, VocabularyTimeoutError
from src.database import init_db

# Configure pytest-asyncio to use function scope for event loops
pytestmark = pytest.mark.asyncio(scope="function")

@pytest.fixture
def agent():
    # Initialize database before running tests
    init_db()
    return Agent()

@pytest.mark.asyncio
async def test_empty_request(agent):
    """Test handling of empty request"""
    with pytest.raises(LyricsError) as exc_info:
        await agent.process_request("")
    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ["empty", "blank", "no request"])

@pytest.mark.asyncio
async def test_lyrics_not_found(agent):
    """Test handling of non-existent song"""
    with patch('src.tools.search_web.search_lyrics', side_effect=LyricsNotFoundError("nonexistent song", "unknown artist")):
        with pytest.raises(LyricsError) as exc_info:
            await agent.process_request("nonexistent song by unknown artist")
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["not found", "no lyrics", "couldn't find"])

@pytest.mark.asyncio
async def test_lyrics_timeout(agent):
    """Test handling of lyrics search timeout"""
    with patch('src.tools.search_web.search_lyrics', side_effect=asyncio.TimeoutError("Lyrics search timed out")):
        with pytest.raises(LyricsError) as exc_info:
            await agent.process_request("timeout by test artist")
        error_msg = str(exc_info.value).lower()
        assert "timed out" in error_msg

@pytest.mark.asyncio
async def test_vocabulary_timeout(agent):
    """Test handling of vocabulary extraction timeout"""
    mock_lyrics = "Sample lyrics for testing"
    
    # Mock successful lyrics search
    with patch('src.tools.search_web.search_lyrics', return_value=mock_lyrics):
        # Mock Ollama timeout
        mock_response = AsyncMock()
        mock_response.side_effect = VocabularyTimeoutError(5)
        
        with patch.object(ollama_client, 'generate', side_effect=mock_response.side_effect):
            with pytest.raises(VocabularyError) as exc_info:
                await agent.process_request("Yesterday by The Beatles")
            error_msg = str(exc_info.value).lower()
            assert "timed out" in error_msg

@pytest.mark.asyncio
async def test_successful_request(agent):
    """Test successful request flow"""
    mock_lyrics = "Yesterday, all my troubles seemed so far away"
    mock_vocab_response = AsyncMock()
    mock_vocab_response.response = '''
    [
        {
            "word": "troubles",
            "context": "Yesterday, all my troubles seemed so far away"
        }
    ]
    '''
    
    # Mock both lyrics search and vocabulary extraction
    with patch('src.tools.search_web.search_lyrics', return_value=mock_lyrics):
        with patch.object(ollama_client, 'generate', return_value=mock_vocab_response):
            result = await agent.process_request("Yesterday by The Beatles")
            assert result["status"] == "success"
            assert result["title"] == "Yesterday"
            assert result["artist"] == "The Beatles"
            assert result["lyrics"] == mock_lyrics
            assert len(result["vocabulary"]) > 0
            assert result["vocabulary"][0]["word"] == "troubles"

@pytest.mark.asyncio
async def test_invalid_song_format(agent):
    """Test handling of invalid song request format"""
    with pytest.raises(LyricsError) as exc_info:
        await agent.process_request("invalid format")
    error_msg = str(exc_info.value).lower()
    assert "invalid" in error_msg or "could not parse" in error_msg

@pytest.mark.asyncio
async def test_error_response_format(agent):
    """Test that error responses have the correct format"""
    with pytest.raises(LyricsError) as exc_info:
        await agent.process_request("")
    e = exc_info.value
    assert hasattr(e, "error_code")
    assert hasattr(e, "http_status")
    assert str(e) is not None

@pytest.mark.asyncio
async def test_concurrent_requests(agent):
    """Test handling of concurrent requests"""
    mock_lyrics = "Sample lyrics for testing"
    mock_vocab_response = AsyncMock()
    mock_vocab_response.response = '''
    [
        {
            "word": "test",
            "context": "Sample lyrics for testing"
        }
    ]
    '''
    
    requests = [
        "Yesterday by The Beatles",
        "Imagine by John Lennon",
        "timeout by test artist",  # Should fail
        "Let It Be by The Beatles"
    ]
    
    # Mock lyrics search to succeed for all except timeout request
    async def mock_search_lyrics(title, artist, timeout=None):
        if "timeout" in title.lower():
            raise asyncio.TimeoutError("Lyrics search timed out")
        return [{
            "title": title,
            "artist": artist,
            "body": mock_lyrics
        }]
    
    with patch('src.tools.search_web.search_lyrics', side_effect=mock_search_lyrics):
        with patch.object(ollama_client, 'generate', return_value=mock_vocab_response):
            tasks = [agent.process_request(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that we got all results
            assert len(results) == len(requests)
            
            # Check that some succeeded
            successes = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
            assert len(successes) > 0
            
            # Check that the timeout request failed
            timeout_result = results[2]  # Index of "timeout by test artist"
            assert isinstance(timeout_result, LyricsError)
            assert "timed out" in str(timeout_result).lower()
