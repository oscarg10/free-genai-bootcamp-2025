"""
Custom exceptions for the Song Vocabulary Extractor.
"""
from typing import Optional

class SongVocabError(Exception):
    """Base exception for all Song Vocabulary Extractor errors."""
    def __init__(self, message: str, error_code: str, http_status: int = 400):
        super().__init__(message)
        self.error_code = error_code
        self.http_status = http_status

class LyricsError(SongVocabError):
    """Raised when there's an error fetching or processing lyrics."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=error_code or 'LYRICS_ERROR',
            http_status=400
        )

class LyricsNotFoundError(LyricsError):
    """Raised when lyrics cannot be found."""
    def __init__(self, title: str, artist: str):
        super().__init__(
            message=f"Could not find lyrics for '{title}' by '{artist}'",
            error_code='LYRICS_NOT_FOUND'
        )

class VocabularyError(SongVocabError):
    """Raised when there's an error processing vocabulary."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=error_code or 'VOCABULARY_ERROR',
            http_status=400
        )

class VocabularyExtractionError(VocabularyError):
    """Raised when vocabulary extraction fails."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code='VOCABULARY_EXTRACTION_ERROR'
        )

class VocabularyTimeoutError(VocabularyError):
    """Raised when vocabulary extraction times out."""
    def __init__(self, timeout: int):
        super().__init__(
            message=f"Vocabulary extraction timed out after {timeout} seconds",
            error_code='VOCABULARY_TIMEOUT'
        )

class StorageError(SongVocabError):
    """Raised when there's an error storing or retrieving data."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=error_code or 'STORAGE_ERROR',
            http_status=500
        )

class InvalidRequestError(SongVocabError):
    """Raised when the request is invalid."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code='INVALID_REQUEST',
            http_status=400
        )
