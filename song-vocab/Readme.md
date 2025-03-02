# Song Vocabulary Extractor

A FastAPI application that extracts vocabulary from song lyrics using AI.

## Features

- Search for song lyrics using DuckDuckGo
- Extract meaningful vocabulary using Mistral 7B
- Store vocabulary in SQLite database
- RESTful API endpoint

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Ollama installed and the Mistral model downloaded:
```bash
ollama pull mistral
```

3. Run the application:
```bash
cd src
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Usage

### POST /api/agent

Request body:
```json
{
    "message_request": "Shape of You Ed Sheeran"
}
```

Response:
```json
{
    "lyrics": "...",
    "vocabulary": [
        {
            "word": "example_word",
            "context": "line where the word appears"
        }
    ]
}
```

## Project Structure

- `src/`
  - `main.py` - FastAPI application
  - `database.py` - SQLite database operations
  - `tools/`
    - `search_web.py` - Web search functionality
    - `get_page_content.py` - Web scraping
    - `extract_vocabulary.py` - AI-powered vocabulary extraction

## Database Schema

The vocabulary is stored in SQLite with the following schema:

- `id`: INTEGER PRIMARY KEY
- `word`: TEXT
- `song_title`: TEXT
- `artist`: TEXT
- `context`: TEXT
- `created_at`: TIMESTAMP