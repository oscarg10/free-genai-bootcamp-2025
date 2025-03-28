# Disable HuggingFace telemetry
import os
import sys
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

import gradio as gr
import requests
import random
import logging
from typing import Tuple, Dict, Any, Optional
from difflib import SequenceMatcher
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# API configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
LANG_PORTAL_URL = os.getenv('LANG_PORTAL_URL', 'http://localhost:5100')
# Set up Flask app and database
sys.path.append(os.path.join(os.path.dirname(__file__), '../lang-portal/backend-flask'))
from lib.db import Db
from flask import Flask

# Initialize Flask app
app = Flask(__name__)

# Set up database path
LANG_PORTAL_DB = os.getenv('LANG_PORTAL_DB', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lang-portal/backend-flask/data/lang_portal.db'))

# Initialize database
db = Db(f'sqlite:///{LANG_PORTAL_DB}')
app.db = db

# Push an application context
app.app_context().push()

# Define app states
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

# Global variables
current_word = None
activity_id = None
group_id = None
session_id = None
current_translation = None
current_state = AppState.SETUP
current_session_id = None
current_word_id = None
current_word_type = None

def create_session() -> int:
    """Create a new study session."""
    global activity_id, group_id
    if not activity_id or not group_id:
        logger.error("Missing activity_id or group_id")
        return None

    try:
        url = f"{LANG_PORTAL_URL}/api/study-sessions"
        data = {"study_activity_id": activity_id, "group_id": group_id}
        logger.info(f"Creating session at {url} with data: {data}")
        response = requests.post(url, json=data)
        logger.info(f"Session creation response: {response.status_code} - {response.text}")
        
        if response.status_code == 201:
            session_id = response.json().get("session_id")
            logger.info(f"Created new session with ID: {session_id}")
            return session_id
        else:
            logger.error(f"Failed to create session: {response.text}")
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
    return None
    return None

def submit_review(word_id: int, correct: bool, session_id: int) -> bool:
    """Submit the review result to the backend."""
    try:
        response = requests.post(
            f"{LANG_PORTAL_URL}/api/study_sessions/{session_id}/review",
            json={
                "word_id": word_id,
                "correct": correct
            }
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error submitting review: {str(e)}")
        return False

def get_german_word() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Get a German word and its English translation using Ollama."""
    global current_word_type
    word_types = ['noun', 'verb', 'adjective']
    word_type = random.choice(word_types)
    current_word_type = word_type
    
    prompt = f"""You are a German language teacher. Generate ONE {word_type} in German with its English translation.
    Requirements:
    1. Common word useful for beginners (A1-A2 level)
    2. Must be different from previous words
    3. Must be a single word (not a phrase)
    
    Format rules:
    - For nouns: Include the article (der/die/das)
    - For verbs: Use the infinitive form
    - For adjectives: Use the basic form
    
    Respond EXACTLY in this format (no other text):
    german: die Katze
    english: cat"""

    try:
        response = requests.post(OLLAMA_API_URL,
            json={
                'model': 'mistral',
                'prompt': prompt,
                'stream': False
            })
        
        if response.status_code == 200:
            result = response.json()['response'].strip()
            # Debug: Print raw response
            logger.debug(f"Raw Ollama response:\n{result}")
            # Parse the response
            lines = result.split('\n')
            if len(lines) >= 2:
                german = lines[0].replace('german:', '').strip()
                english = lines[1].replace('english:', '').strip()
                # Clean up any extra quotes
                german = german.strip('"').strip("'").strip()
                english = english.strip('"').strip("'").strip()
                
                # Detect word type from the German word
                detected_type = word_type
                if german.startswith(('der ', 'die ', 'das ')):
                    detected_type = 'noun'
                elif german.endswith('en'):
                    detected_type = 'verb'
                else:
                    detected_type = 'adjective'
                
                logger.info(f"Generated {detected_type}: {german} ({english})")
                return german, english, detected_type
            else:
                logger.error("Unexpected response format from Ollama")
                return None, None, None
        else:
            logger.error(f"Ollama request failed: {response.status_code}")
            return None, None, None
    except Exception as e:
        logger.error(f"Error generating word with Ollama: {str(e)}")
        return None, None, None

def evaluate_translation(user_translation: str, session_id: int) -> str:
    """Evaluate the user's translation."""
    try:
        if not current_word:
            return "No word to translate. Click 'New Word' to start."
        
        german_word, correct_translation = current_word
        user_translation = user_translation.strip().lower()
        correct_translation = correct_translation.strip().lower()
        
        # Exact match required
        is_correct = user_translation == correct_translation
        
        feedback = f"Your translation: {user_translation}\n"
        feedback += f"Correct translation: {correct_translation}\n\n"
        
        if is_correct:
            feedback += "Correct! Perfect translation!"
        else:
            feedback += "Incorrect. Try again!"
            
            # Store incorrect word in practice_words table
            if session_id:
                logger.info(f"Storing incorrect word: {german_word} (session_id={session_id})")
                try:
                    with app.app_context():
                        with db.get() as conn:
                            # Determine word groups based on type and meaning
                            word_groups = ['Basic Vocabulary']  # Always add to basic vocabulary
                            
                            # Add to type-specific groups
                            if current_word_type == 'noun':
                                # Try to categorize nouns based on meaning
                                if any(word in correct_translation.lower() for word in ['food', 'drink', 'meal', 'eat']):
                                    word_groups.append('Food & Drink')
                                elif any(word in correct_translation.lower() for word in ['mother', 'father', 'sister', 'brother', 'aunt', 'uncle']):
                                    word_groups.append('Family')
                                elif any(word in correct_translation.lower() for word in ['doctor', 'teacher', 'engineer', 'worker']):
                                    word_groups.append('Professions')
                                elif any(word in correct_translation.lower() for word in ['head', 'arm', 'leg', 'body', 'health']):
                                    word_groups.append('Body & Health')
                            elif current_word_type == 'adjective':
                                # Categorize adjectives
                                if any(word in correct_translation.lower() for word in ['red', 'blue', 'green', 'yellow', 'round', 'square']):
                                    word_groups.append('Colors & Shapes')
                                elif any(word in correct_translation.lower() for word in ['happy', 'sad', 'angry', 'excited']):
                                    word_groups.append('Emotions')
                                elif any(word in correct_translation.lower() for word in ['hot', 'cold', 'warm', 'sunny', 'rainy']):
                                    word_groups.append('Weather')
                            
                            # Add the word with its groups
                            db.add_practice_word(
                                session_id=session_id,
                                german_word=german_word,
                                english_translation=correct_translation,
                                word_type=current_word_type,
                                word_groups=word_groups
                            )
                        logger.info(f"Successfully stored incorrect word: {german_word}")
                except Exception as e:
                    logger.error(f"Failed to store incorrect word: {str(e)}")
            else:
                logger.error("No session_id available. Word will not be stored.")
        
        return feedback
    except Exception as e:
        logger.error(f"Error evaluating translation: {str(e)}")
        return f"Error evaluating translation: {str(e)}"

def on_submit(translation: str, session_id: int):
    """Handle translation submission."""
    if not translation:
        return "", "Please enter a translation"
    
    feedback = evaluate_translation(translation, session_id)
    return "", feedback

def on_new_word():
    """Get a new word and reset the interface."""
    global current_word
    word, translation, word_type = get_german_word()
    if word and translation:
        current_word = (word, translation)
        return gr.update(value=f"{word} ({word_type})"), gr.update(value=""), ""
    return gr.update(value="Error getting word"), gr.update(value=""), "Could not get a new word. Please try again."

def load_session(request: gr.Request):
    """Load session from URL parameters."""
    global activity_id, group_id, current_session_id
    try:
        # Get parameters from URL
        params = request.query_params
        logger.info(f"Attempting to load session with params: {params}")
        
        # Get activity_id and group_id
        activity_id = params.get('activity_id')
        group_id = params.get('group_id')
        
        if not activity_id or not group_id:
            logger.warning("Missing activity_id or group_id")
            return None, None
        
        # Convert to integers
        try:
            activity_id = int(activity_id)
            group_id = int(group_id)
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid activity_id or group_id: {e}")
            return None, None

        logger.info(f"Loading session for activity {activity_id} and group {group_id}")
        
        # Create a new session
        session_id = create_session()
        if session_id:
            # Set the global current_session_id
            current_session_id = session_id
            logger.info(f"Created session {session_id} for activity {activity_id} and group {group_id}")
            return activity_id, group_id
        else:
            logger.error("Failed to create session")
            return None, None
    except Exception as e:
        logger.error(f"Error loading session: {str(e)}")
        return None, None

def on_session_load(activity_id, group_id):
    """Handle session loading."""
    if activity_id and group_id:
        word, translation, word_type = get_german_word()
        return [f"{word} ({word_type})", "", gr.update(interactive=True), ""]
    return ["Please launch from the main portal", "", gr.update(interactive=False), ""]

# Create Gradio interface
with gr.Blocks(title="German Word Translation Practice") as demo:
    # Get activity_id, group_id, and session_id from URL parameters
    activity_id_state = gr.State(value=None)
    group_id_state = gr.State(value=None)
    session_id_state = gr.State(value=None)
    
    def load_session(request: gr.Request):
        global activity_id, group_id
        try:
            # Get parameters from URL
            params = request.query_params
            logger.info(f"Attempting to load session with params: {params}")
            
            # Get activity_id and group_id
            activity_id = params.get('activity_id')
            group_id = params.get('group_id')
            
            if not activity_id or not group_id:
                logger.warning("Missing activity_id or group_id")
                return None, None, None
            
            # Convert to integers
            try:
                activity_id = int(activity_id)
                group_id = int(group_id)
            except (TypeError, ValueError) as e:
                logger.error(f"Invalid activity_id or group_id: {e}")
                return None, None, None

            logger.info(f"Loading session for activity {activity_id} and group {group_id}")
            
            # Create a new session
            session_id = create_session()
            if session_id:
                logger.info(f"Created session {session_id}")
                return activity_id, group_id, session_id
            else:
                logger.error("Failed to create session")
                return None, None, None
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return None, None, None
    
    # Create welcome message
    welcome_msg = gr.Markdown("""
    # Welcome to German Word Translation Practice
    
    Practice translating German words to English! Click 'New Word' to get started.
    """, visible=True)
    
    # Load session and hide welcome message if successful
    def on_session_load(activity_id, group_id, session_id):
        if activity_id and group_id and session_id:
            return gr.update(visible=False)
        return gr.update(visible=True)
    
    demo.load(load_session, outputs=[activity_id_state, group_id_state, session_id_state]).then(
        fn=on_session_load,
        inputs=[activity_id_state, group_id_state, session_id_state],
        outputs=[welcome_msg]
    )
    
    # Create practice interface
    with gr.Column() as practice_ui:
        # Word display
        word_display = gr.Text(label="German Word", interactive=False)
        
        # Translation input
        translation_input = gr.Text(
            label="Your English Translation",
            placeholder="Type your English translation here...",
            interactive=True
        )
        
        # Feedback display
        feedback_display = gr.Text(
            label="Feedback",
            interactive=False,
            max_lines=10
        )
        
        # Buttons
        with gr.Row():
            new_word_btn = gr.Button("New Word")
            submit_btn = gr.Button("Check Translation", variant="primary")
    
    # Event handlers
    new_word_btn.click(
        fn=on_new_word,
        outputs=[
            word_display,
            translation_input,
            feedback_display
        ]
    )
    
    submit_btn.click(
        fn=on_submit,
        inputs=[translation_input, session_id_state],
        outputs=[translation_input, feedback_display]
    )
    
    # Also submit on Enter key
    translation_input.submit(
        fn=on_submit,
        inputs=[translation_input, session_id_state],
        outputs=[translation_input, feedback_display]
    )

def test_ollama_integration():
    """Test Ollama integration for word generation."""
    print("Testing Ollama word generation...")
    word, translation, word_type = get_german_word()
    if word and translation:
        print(f"Generated word: {word}")
        print(f"Translation: {translation}")
        print(f"Word type: {word_type}")
    else:
        print("Failed to generate word")

def get_word_groups():
    """Get all available word groups."""
    with app.app_context():
        with db.get() as conn:
            return db.get_word_groups()

def get_words_in_group(group_id: int):
    """Get all words in a specific word group."""
    with app.app_context():
        with db.get() as conn:
            return db.get_words_in_group(group_id)

if __name__ == "__main__":
    test_ollama_integration()
    demo.launch(server_port=7860)