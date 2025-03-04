import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.tools.extract_vocabulary import extract_vocabulary, VocabularyItem, client
from src.exceptions import VocabularyError

SAMPLE_LYRICS = """
Yesterday all my troubles seemed so far away.
Now it looks as though they're here to stay.
Oh, I believe in yesterday.
"""

@pytest.mark.asyncio
async def test_empty_lyrics():
    """Test handling of empty lyrics"""
    with pytest.raises(VocabularyError) as exc_info:
        await extract_vocabulary("")
    assert "empty lyrics" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling"""
    mock_response = AsyncMock()
    # Make the mock sleep for longer than the timeout
    mock_response.side_effect = asyncio.sleep(0.2)
    
    with patch.object(client, 'generate', return_value=mock_response):
        with pytest.raises(VocabularyError) as exc_info:
            await extract_vocabulary(SAMPLE_LYRICS, timeout=0.1)
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["timeout", "timed out"])
        assert getattr(exc_info.value, "error_code", "") == "VOCAB_TIMEOUT"

@pytest.mark.asyncio
async def test_successful_extraction():
    """Test successful vocabulary extraction"""
    mock_response = AsyncMock()
    mock_response.response = '''
    [
        {
            "word": "troubles",
            "context": "Yesterday all my troubles seemed so far away"
        },
        {
            "word": "yesterday",
            "context": "Oh, I believe in yesterday"
        }
    ]
    '''
    
    with patch.object(client, 'generate', return_value=mock_response):
        items = await extract_vocabulary(SAMPLE_LYRICS)
        assert len(items) == 2
        assert all(isinstance(item, VocabularyItem) for item in items)
        assert items[0].word == "troubles"
        assert items[1].word == "yesterday"

@pytest.mark.asyncio
async def test_vocabulary_item_serialization():
    """Test VocabularyItem serialization"""
    mock_response = AsyncMock()
    mock_response.response = '''
    [
        {
            "word": "troubles",
            "context": "Yesterday all my troubles seemed so far away"
        }
    ]
    '''
    
    with patch.object(client, 'generate', return_value=mock_response):
        items = await extract_vocabulary(SAMPLE_LYRICS)
        for item in items:
            dict_form = item.dict()
            assert isinstance(dict_form, dict)
            assert "word" in dict_form
            assert "context" in dict_form

@pytest.mark.asyncio
async def test_concurrent_extraction():
    """Test concurrent vocabulary extraction"""
    mock_response = AsyncMock()
    mock_response.response = '''
    [
        {
            "word": "test",
            "context": "Test context"
        }
    ]
    '''
    
    lyrics_list = [
        SAMPLE_LYRICS,
        "Different lyrics for testing",
        "More sample lyrics here"
    ]
    
    with patch.object(client, 'generate', return_value=mock_response):
        tasks = [extract_vocabulary(lyrics) for lyrics in lyrics_list]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == len(lyrics_list)
        assert all(len(items) > 0 for items in results)

@pytest.mark.asyncio
async def test_invalid_lyrics():
    """Test handling of invalid lyrics"""
    mock_response = AsyncMock()
    mock_response.response = "[]"
    
    invalid_inputs = [
        None,
        "",
        " ",
        "\n\n\n",
        "a"  # Too short to extract vocabulary
    ]
    
    with patch.object(client, 'generate', return_value=mock_response):
        for lyrics in invalid_inputs:
            with pytest.raises(VocabularyError):
                await extract_vocabulary(lyrics)
                
@pytest.mark.asyncio
async def test_invalid_ollama_response():
    """Test handling of invalid response from Ollama"""
    mock_response = AsyncMock()
    mock_response.response = "Not a JSON response"
    
    with patch.object(client, 'generate', return_value=mock_response):
        with pytest.raises(VocabularyError) as exc_info:
            await extract_vocabulary(SAMPLE_LYRICS)
        assert "Could not find JSON array" in str(exc_info.value)
        
@pytest.mark.asyncio
async def test_invalid_json_structure():
    """Test handling of invalid JSON structure from Ollama"""
    mock_response = AsyncMock()
    mock_response.response = '''
    [
        {
            "invalid_field": "test"
        }
    ]
    '''
    
    with patch.object(client, 'generate', return_value=mock_response):
        with pytest.raises(VocabularyError) as exc_info:
            await extract_vocabulary(SAMPLE_LYRICS)
        assert "No valid vocabulary items found" in str(exc_info.value)
