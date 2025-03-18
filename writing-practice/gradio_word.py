# Disable HuggingFace telemetry
import os
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
OLLAMA_API_URL = 'http://localhost:11434/api/generate'

# API configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
LANG_PORTAL_URL = os.getenv('LANG_PORTAL_URL', 'http://localhost:5000')

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

def create_session() -> int:
    """Create a new study session."""
    global activity_id, group_id
    if not activity_id or not group_id:
        logger.error("Missing activity_id or group_id")
        return None

    try:
        response = requests.post(
            f"{LANG_PORTAL_URL}/api/study_sessions",
            json={
                "study_activity_id": activity_id,
                "group_id": group_id
            }
        )
        if response.status_code == 201:
            return response.json().get("session_id")
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
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

def get_german_word() -> Tuple[Optional[str], Optional[str]]:
    """Get a German word and its English translation using Ollama."""
    prompt = """Generate a common German word suitable for language learning.
    The word should be:
    1. Easy to understand
    2. Common in everyday use
    3. Basic vocabulary level
    
    Format your response exactly like this example:
    german: Katze
    english: cat
    
    Only return the word pair in this format, nothing else."""

    try:
        response = requests.post(OLLAMA_API_URL,
            json={
                'model': 'mistral',
                'prompt': prompt,
                'stream': False
            })
        
        if response.status_code == 200:
            result = response.json()['response'].strip()
            # Parse the response
            lines = result.split('\n')
            if len(lines) >= 2:
                german = lines[0].replace('german:', '').strip()
                english = lines[1].replace('english:', '').strip()
                # Clean up any extra quotes
                german = german.strip('"').strip("'").strip()
                english = english.strip('"').strip("'").strip()
                logger.info(f"Ollama generated word pair: {german} ({english})")
                return german, english
            else:
                logger.error("Unexpected response format from Ollama")
                return None, None
        else:
            logger.error(f"Ollama request failed: {response.status_code}")
            return None, None
    except Exception as e:
        logger.exception("Error generating word with Ollama:")
        return None, None

def evaluate_translation(user_translation: str) -> Tuple[bool, str]:
    """Evaluate the user's translation."""
    global current_word, current_translation, current_state, current_session_id, current_word_id
    
    if not current_word or not current_translation:
        return False, "Please generate a new word first"
    
    # Calculate similarity with the correct translation
    similarity = SequenceMatcher(None, user_translation.lower(), current_translation.lower()).ratio()
    is_correct = similarity >= 0.8
    
    # Get feedback from Ollama
    prompt = f"""Evaluate this German-English translation:
    German word: {current_word}
    Correct translation: {current_translation}
    User's translation: {user_translation}
    Similarity score: {similarity:.2f}

    Give brief, encouraging feedback in 1-2 sentences. If there are mistakes, explain what's wrong.
    Be friendly but professional."""

    try:
        response = requests.post(OLLAMA_API_URL,
            json={
                'model': 'mistral',
                'prompt': prompt,
                'stream': False
            })
        
        if response.status_code == 200:
            feedback = response.json()['response'].strip()
            feedback = feedback.strip('"').strip("'").strip()
        else:
            feedback = "Correct!" if is_correct else f"Not quite. The correct translation is: {current_translation}"
    except Exception as e:
        logger.error(f"Error getting feedback from Ollama: {str(e)}")
        feedback = "Correct!" if is_correct else f"Not quite. The correct translation is: {current_translation}"
    
    # Submit the result to the backend if we have a session ID
    if current_session_id and current_word_id:
        if submit_review(current_word_id, is_correct, current_session_id):
            feedback += "\nResult saved successfully"
        else:
            feedback += "\nWarning: Could not save result"
    
    current_state = AppState.REVIEW
    return is_correct, feedback

def on_new_word():
    """Reset the interface for a new word."""
    global current_word, current_translation, current_session_id, current_state
    
    # Create a new session if we don't have one
    if not current_session_id:
        current_session_id = create_session()
        if not current_session_id:
            return ["Error: Could not create session", "", gr.update(interactive=False), ""]
    
    # Get a new word from Ollama
    word, translation = get_german_word()
    if not word or not translation:
        return ["Error: Could not generate word", "", gr.update(interactive=False), ""]
    
    current_word = word
    current_translation = translation
    current_state = AppState.PRACTICE
    
    return [word, "", gr.update(interactive=True), ""]

def on_submit(translation: str):
    """Handle translation submission."""
    if not translation:
        return [gr.update(interactive=True), "Please enter a translation"]
    
    is_correct, feedback = evaluate_translation(translation)
    return [gr.update(interactive=True), feedback]

def load_session(request: gr.Request):
    """Load session from URL parameters."""
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
            return None, None
        
        # Convert to integers
        try:
            activity_id = int(activity_id)
            group_id = int(group_id)
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid activity_id or group_id: {e}")
            return None, None

        logger.info(f"Loading session for activity {activity_id} and group {group_id}")
        return activity_id, group_id
    except Exception as e:
        logger.error(f"Error loading session: {str(e)}")
        return None, None

def on_session_load(activity_id, group_id):
    """Handle session loading."""
    if activity_id and group_id:
        word, translation = get_german_word()
        return [word, "", gr.update(interactive=True), ""]
    return ["Please launch from the main portal", "", gr.update(interactive=False), ""]

# Create Gradio interface
with gr.Blocks(title="German Word Translation Practice") as demo:
    # Get activity_id and group_id from URL parameters
    activity_id_state = gr.State(value=None)
    group_id_state = gr.State(value=None)
    
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
                return None, None
            
            # Convert to integers
            try:
                activity_id = int(activity_id)
                group_id = int(group_id)
            except (TypeError, ValueError) as e:
                logger.error(f"Invalid activity_id or group_id: {e}")
                return None, None

            logger.info(f"Loading session for activity {activity_id} and group {group_id}")
            return activity_id, group_id
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return None, None
    
    # Create welcome message
    welcome_msg = gr.Markdown("""
    # Welcome to German Word Translation Practice
    
    Practice translating German words to English! Click 'New Word' to get started.
    """, visible=True)
    
    # Load session and hide welcome message if successful
    def on_session_load(activity_id, group_id):
        if activity_id and group_id:
            return gr.update(visible=False)
        return gr.update(visible=True)
    
    demo.load(load_session, outputs=[activity_id_state, group_id_state]).then(
        fn=on_session_load,
        inputs=[activity_id_state, group_id_state],
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
    def on_new_word():
        """Get a new word and reset the interface."""
        word, translation = get_german_word()
        if word and translation:
            global current_word
            current_word = (word, translation)
            return [
                word,           # word_display
                "",            # translation_input
                ""             # feedback_display
            ]
        return [
            "Error getting word",
            "",
            "Could not get a new word. Please try again."
        ]
    
    new_word_btn.click(
        fn=on_new_word,
        outputs=[
            word_display,
            translation_input,
            feedback_display
        ]
    )
    
    submit_btn.click(
        fn=evaluate_translation,
        inputs=[translation_input],
        outputs=[feedback_display]
    )

def test_ollama_integration():
    """Test Ollama integration for word generation."""
    print("Testing Ollama word generation...")
    word, translation = get_german_word()
    if word and translation:
        print(f"Generated word: {word}")
        print(f"Translation: {translation}")
    else:
        print("Failed to generate word")

if __name__ == "__main__":
    test_ollama_integration()
    demo.launch()