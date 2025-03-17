# Disable HuggingFace telemetry
import os
import dotenv
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

import gradio as gr
import requests
import random
import logging
from typing import Tuple, Dict, Any, Optional
from transformers import pipeline, set_seed
import torch
from difflib import SequenceMatcher
from enum import Enum

# Load environment variables
dotenv.load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# API configuration
OLLAMA_API_URL = 'http://localhost:11434/api/generate'

def get_english_word(word_type: str) -> Tuple[str, str]:
    """Get a natural English word and generate a sentence using Ollama."""
    prompt = f"""First generate a common {word_type} in English that would be good for language learning.
    Then generate a simple natural sentence using that word.
    The sentence should be:
    1. Easy to understand
    2. Suitable for language learning
    3. Use common vocabulary
    4. Be between 5-10 words
    5. Use present tense

    Format your response exactly like this example:
    word: cat
    sentence: The cat sleeps on the warm windowsill.

    Only return the word and sentence in this format, nothing else."""

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
                word = lines[0].replace('word:', '').strip()
                sentence = lines[1].replace('sentence:', '').strip()
                # Clean up any extra quotes or periods
                word = word.strip('"').strip("'").strip()
                sentence = sentence.strip('"').strip("'").strip()
                if not sentence.endswith('.'):
                    sentence += '.'
                logger.info(f"Ollama generated word: {word} and sentence: {sentence}")
                return word, sentence
            else:
                logger.error("Unexpected response format from Ollama")
                return None, None
        else:
            logger.error(f"Ollama request failed: {response.status_code}")
            return None, None
    except Exception as e:
        logger.exception("Error generating word and sentence with Ollama:")
        return None, None

# Debug environment variables
logger.debug("Environment variables:")
logger.debug(f"OLLAMA_API_URL: {OLLAMA_API_URL}")

# Verify API connection
try:
    logger.debug(f"Making test request to {OLLAMA_API_URL}")
    test_response = requests.post(OLLAMA_API_URL,
        json={
            'model': 'mistral',
            'prompt': 'Test prompt',
            'stream': False
        })
    logger.info(f"API Test Response: {test_response.status_code}")
    logger.info(f"API Test Response Text: {test_response.text}")
    if test_response.status_code == 200:
        logger.info("API connection successful!")
    else:
        logger.error(f"API test failed with status {test_response.status_code}")
except Exception as e:
    logger.error(f"API test failed with error: {str(e)}")

# Define app states
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

# Global variables
current_sentence = None
current_state = AppState.SETUP
current_english_sentence = None
session_id = None  # Track the current study session

# Initialize translation pipelines
try:
    # English to German translator
    en_de_translator = pipeline(
        "translation",
        model="Helsinki-NLP/opus-mt-en-de",
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    logger.info("Translation models loaded successfully")
except Exception as e:
    logger.error(f"Error loading translation models: {str(e)}")
    en_de_translator = None

# Set random seed for reproducibility
set_seed(42)

def get_word_and_sentence() -> str:
    """Fetch a random word and generate an English practice sentence."""
    global current_sentence, current_state, current_english_sentence
    
    try:
        logger.debug("Starting get_word_and_sentence function")
        
        # Fetch vocabulary from backend
        logger.info(f"Fetching words for practice")
        word_type = random.choice(['noun', 'verb', 'adjective'])
        english_word, english_sentence = get_english_word(word_type)
        if not english_word:
            logger.error("Failed to get word and sentence from Ollama")
            return "Failed to get word and sentence"
        
        current_english_sentence = english_sentence
        
        # Get the German translation for evaluation
        if en_de_translator:
            logger.debug(f"Translating English sentence to German: {english_sentence}")
            translation_result = en_de_translator(english_sentence, max_length=50)[0]
            german_translation = translation_result['translation_text']
            current_sentence = german_translation
            logger.info(f"English sentence translated to German: {german_translation}")
        else:
            logger.error("English to German translator not available")
            current_sentence = "Translation model not available"
        
        # Update state to practice
        current_state = AppState.PRACTICE
        
        return english_sentence
        
    except Exception as e:
        logger.exception("Error in get_word_and_sentence:")
        return f"Error: {str(e)}"

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def evaluate_translation(user_translation: str) -> str:
    """Evaluate the user's German translation."""
    global current_sentence, current_state
    
    try:
        logger.debug("Starting translation evaluation")
        
        if not current_sentence:
            logger.error("No current sentence available for evaluation")
            return "Please generate a new sentence first"
        
        if not user_translation:
            logger.error("No user translation provided")
            return "Please enter your translation"
        
        logger.info(f"Evaluating translation:")
        logger.info(f"Expected German: {current_sentence}")
        logger.info(f"User's German:  {user_translation}")
        
        # Calculate similarity score
        similarity = calculate_similarity(user_translation, current_sentence)
        score = int(similarity * 100)
        logger.info(f"Similarity score: {score}%")
        
        # Get literal translation of user's text for comparison
        if en_de_translator:
            logger.debug(f"Translating user's German text to English")
            translation_result = en_de_translator(user_translation, max_length=50)[0]
            user_translation_in_english = translation_result['translation_text']
            logger.info(f"User's translation in English: {user_translation_in_english}")
        else:
            logger.error("Translation model not available for user's text")
            user_translation_in_english = "Translation not available"
        
        # Determine grade and feedback
        if score >= 90:
            grade = "A"
            feedback = "Excellent! Your translation is very accurate."
        elif score >= 80:
            grade = "B"
            feedback = "Good job! Just a few minor differences."
        elif score >= 60:
            grade = "C"
            feedback = "Keep practicing! Pay attention to grammar and word choice."
        else:
            grade = "D"
            feedback = "Try again. Make sure to check your German grammar and vocabulary."
        
        logger.info(f"Grade: {grade}")
        
        # Update state to review
        current_state = AppState.REVIEW
        
        feedback_text = f"""Your translation: {user_translation}
Correct German: {current_sentence}
Your translation in English: {user_translation_in_english}
Correct English: {current_english_sentence}

Score: {score}%
Grade: {grade}
{feedback}"""
        
        return feedback_text
        
    except Exception as e:
        logger.exception("Error in translation evaluation:")
        return f"Error evaluating translation: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="German Translation Practice") as demo:
    # Get session_id and group_id from URL parameters
    session_id = gr.State(value=None)
    group_id = gr.State(value=None)
    
    def load_session(request: gr.Request):
        global session_id, current_state, group_id
        try:
            # Get parameters from URL
            params = request.query_params
            logger.info(f"Attempting to load session with params: {params}")
            
            # Get session_id and group_id
            session_id = params.get('session_id')
            group_id = params.get('group_id')
            
            if not session_id or not group_id:
                logger.warning("Missing session_id or group_id, showing welcome message")
                return None, None
            # Convert to integers
            try:
                session_id = int(session_id)
                group_id = int(group_id)
            except (TypeError, ValueError) as e:
                logger.error(f"Invalid session_id or group_id: {e}")
                return None, None

            logger.info(f"Loading session {session_id} for group {group_id}")
            current_state = AppState.PRACTICE
            return session_id, group_id
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return None, None
    
    # Create welcome message
    welcome_msg = gr.Markdown("""
    # Welcome to German Translation Practice
    
    Practice translating English sentences to German! Click 'New Sentence' to get started.
    """, visible=True)
    
    # Load session and hide welcome message if successful
    def on_session_load(session_id, group_id):
        if session_id and group_id:
            return gr.update(visible=False)
        return gr.update(visible=True)
    
    demo.load(load_session, outputs=[session_id, group_id]).then(
        fn=on_session_load,
        inputs=[session_id, group_id],
        outputs=[welcome_msg]
    )
    
    gr.Markdown("# German Translation Practice")
    
    # Create interface elements
    with gr.Row():
        english_sentence = gr.Text(label="English Sentence", interactive=False)
    
    with gr.Row():
        user_translation = gr.Text(
            label="Your German Translation",
            placeholder="Type your German translation here...",
            interactive=True
        )
    
    with gr.Row():
        feedback_display = gr.Text(
            label="Feedback",
            interactive=False,
            max_lines=10
        )
    
    with gr.Row():
        new_sentence_btn = gr.Button("New Sentence")
        submit_btn = gr.Button("Check Translation", variant="primary")
    
    # Set up event handlers
    def on_new_question():
        """Reset the interface for a new question."""
        return [
            "",  # user_translation
            ""   # feedback_display
        ]
    
    def on_submit():
        """Update interface after submission."""
        return [
            gr.update(interactive=False),  # submit_btn
            gr.update(interactive=True)     # new_sentence_btn
        ]
    
    new_sentence_btn.click(
        fn=get_word_and_sentence,
        inputs=[],  # No inputs needed since we use global group_id
        outputs=[english_sentence]
    ).then(
        fn=lambda: [
            gr.update(interactive=True),  # submit_btn
            gr.update(interactive=False),  # new_sentence_btn
            "",  # user_translation
            ""   # feedback_display
        ],
        outputs=[
            submit_btn,
            new_sentence_btn,
            user_translation,
            feedback_display
        ]
    )
    
    submit_btn.click(
        fn=evaluate_translation,
        inputs=[user_translation],
        outputs=[feedback_display]
    ).then(
        fn=on_submit,
        outputs=[
            submit_btn,
            new_sentence_btn
        ]
    )

def test_ollama_integration():
    """Test Ollama integration with different word types."""
    word_types = ['noun', 'verb', 'adjective']
    
    print("Testing Ollama integration...")
    for word_type in word_types:
        print(f"\nTesting with {word_type}:")
        word, sentence = get_english_word(word_type)
        if word and sentence:
            print(f"Word: {word}")
            print(f"Sentence: {sentence}")
        else:
            print(f"Failed to get {word_type}")

if __name__ == "__main__":
    test_ollama_integration()
    demo.launch()