# Disable HuggingFace telemetry
import os
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

import gradio as gr
import requests
import random
import logging
from typing import Tuple, Dict, Any
from transformers import pipeline, set_seed
import torch
import easyocr
import numpy as np
from difflib import SequenceMatcher
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Initialize translation pipeline
try:
    translator = pipeline(
        "translation",
        model="Helsinki-NLP/opus-mt-en-de",
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    logger.info("Translation model loaded successfully")
except Exception as e:
    logger.error(f"Error loading translation model: {str(e)}")
    translator = None

# Initialize OCR reader
try:
    reader = easyocr.Reader(['de'])  # Initialize for German
    logger.info("OCR model loaded successfully")
except Exception as e:
    logger.error(f"Error loading OCR model: {str(e)}")
    reader = None

# Set random seed for reproducibility
set_seed(42)

# Template sentences for different word types
SENTENCE_TEMPLATES = {
    "noun": [
        "Ich sehe {}.",  # I see ...
        "Das ist {}.",   # This is ...
        "Hier ist {}.",  # Here is ...
        "Ich habe {}.",  # I have ...
    ],
    "verb": [
        "Ich {} gerne.",      # I like to ...
        "Wir {} heute.",      # We ... today
        "Sie {} auch.",       # She/They ... too
        "Ich möchte {}.",     # I want to ...
    ],
    "adjective": [
        "Das ist {}.",        # This is ...
        "Es ist sehr {}.",    # It is very ...
        "Ich bin {}.",        # I am ...
        "Das Wetter ist {}.", # The weather is ...
    ]
}

def get_word_and_sentence() -> Tuple[str, str]:
    """Fetch a random word and generate a practice sentence."""
    global current_sentence, current_state, current_english_sentence, group_id
    
    try:
        # We already have a session_id and group_id from the URL parameters
        if not session_id:
            return "Error", "No session ID found. Please launch from the main app."
            
        if not group_id:
            return "Error", "No group ID found. Please launch from the main app."
        
        # Fetch vocabulary from backend
        logger.info(f"Fetching words for group_id: {group_id} (type: {type(group_id)})")
        response = requests.get(
            "http://localhost:5100/api/study-activities/words",
            params={"group_id": str(group_id)}  # Convert to string for URL params
        )
        
        if response.status_code != 200:
            return "Error", f"Failed to fetch words. Status: {response.status_code}"
        
        words = response.json().get('words', [])
        if not words:
            return "Error", "No words found in vocabulary"
        
        # Select random word
        word = random.choice(words)
        german_word = word['german']  # Now includes article if it's a noun
        word_type = word['word_type'].lower()
        
        # Generate a simple sentence using templates
        templates = SENTENCE_TEMPLATES.get(word_type, SENTENCE_TEMPLATES['noun'])
        template = random.choice(templates)
        
        # For nouns, the article is already included in german_word
        sentence = template.format(german_word)
        
        # Store the current sentence for evaluation
        current_sentence = sentence
        
        # Translate the sentence to English for reference
        if translator:
            translation = translator(sentence, max_length=50)[0]['translation_text']
            current_english_sentence = translation
        else:
            translation = "Translation model not available"
            current_english_sentence = translation
        
        # Update state to practice
        current_state = AppState.PRACTICE
        
        output = f"English: {translation}"  # Only show English sentence as per specs
        return "", output  # Clear word display, show only English sentence
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return "Error", str(e)

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def evaluate_handwriting(image_path) -> Tuple[str, str]:
    """Evaluate the handwritten text using OCR."""
    global current_sentence, current_state
    try:
        if not reader:
            return "Error", "OCR model not available"
        
        if not current_sentence:
            return "Error", "Please generate a new sentence first"
        
        # Debug image format
        logger.info(f"Image path type: {type(image_path)}")
        
        # Check if we have a valid image path
        if not image_path:
            return "Error", "No image provided"
        
        # Since we set type="filepath", we get the path directly
        logger.info(f"Processing image from path: {image_path}")
        
        # Perform OCR directly on the file path
        results = reader.readtext(image_path)
        
        if not results:
            return "Error", "No text detected in the image"
        
        # Extract text from OCR results
        detected_text = ' '.join([result[1] for result in results])
        logger.info(f"Detected text: {detected_text}")
        
        # Get literal translation of detected text
        if translator:
            detected_translation = translator(detected_text, max_length=50)[0]['translation_text']
        else:
            detected_translation = "Translation not available"
        
        # Calculate similarity score and determine grade
        similarity = calculate_similarity(detected_text, current_sentence)
        score = int(similarity * 100)
        
        if score >= 90:
            grade = "A"
            feedback = "Excellent! Your sentence is very accurate."
        elif score >= 80:
            grade = "B"
            feedback = "Good job! Just a few minor differences."
        elif score >= 60:
            grade = "C"
            feedback = "Keep practicing! Pay attention to spelling and umlauts."
        else:
            grade = "D"
            feedback = "Try again. Make sure to write clearly and check your spelling."
        
        # Update state to review
        current_state = AppState.REVIEW
        
        feedback_text = f"""Transcript: {detected_text}
Translation: {detected_translation}

Grade: {grade}
{feedback}"""
        
        return grade, feedback_text
        
    except Exception as e:
        logger.error(f"Error evaluating handwriting: {str(e)}")
        return "F", f"Error processing handwriting: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="German Writing Practice") as demo:
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
    # Welcome to German Writing Practice
    
    Please launch this app from the main application.
    If you arrived here directly, go back and click the 'Launch' button.
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
    
    gr.Markdown("# German Writing Practice")
    
    # Create state-dependent components
    with gr.Row():
        word_display = gr.Textbox(label="Word to Practice", visible=False)
        sentence_display = gr.Textbox(label="English Sentence", lines=3)
    
    with gr.Row():
        with gr.Column():
            canvas = gr.Image(
                type="filepath",  # Accept uploaded files
                label="Upload your handwritten German sentence",
                height=200,
                width=400,
                sources=["upload"]  # Only allow uploads, no webcam or sketching
            )
            submit_btn = gr.Button("Submit for Review")
    
    with gr.Row():
        grade_display = gr.Textbox(label="Grade")
        feedback_display = gr.Textbox(label="Feedback", lines=4)
    
    with gr.Row():
        new_word_btn = gr.Button("Generate Sentence")
        next_btn = gr.Button("Next Question", visible=False)
    
    # Set up event handlers
    def on_new_question():
        """Reset the interface for a new question."""
        # Create a fresh Image component
        new_canvas = gr.Image(
            type="filepath",
            label="Upload your handwritten German sentence",
            height=200,
            width=400,
            sources=["upload"],
            visible=True,
            interactive=True
        )
        return [
            "",  # grade
            "",  # feedback
            new_canvas,  # new upload component
            gr.update(visible=False),  # hide next button
            new_canvas  # update canvas again
        ]
    
    def on_submit():
        """Update interface after submission."""
        new_canvas = gr.Image(
            type="filepath",
            label="Upload your handwritten German sentence",
            height=200,
            width=400,
            sources=["upload"],
            visible=True,
            interactive=True
        )
        return [
            gr.update(visible=True),  # show next button
            new_canvas  # new upload component
        ]
    
    new_word_btn.click(
        fn=get_word_and_sentence,
        inputs=[],  # No inputs needed since we use global group_id
        outputs=[word_display, sentence_display]
    ).then(
        fn=on_new_question,
        outputs=[grade_display, feedback_display, canvas, next_btn, canvas]
    )
    
    next_btn.click(
        fn=get_word_and_sentence,
        outputs=[word_display, sentence_display]
    ).then(
        fn=on_new_question,
        outputs=[grade_display, feedback_display, canvas, next_btn, canvas]
    )
    
    submit_btn.click(
        fn=evaluate_handwriting,
        inputs=[canvas],
        outputs=[grade_display, feedback_display]
    ).then(
        fn=on_submit,
        outputs=[next_btn, canvas]
    )

if __name__ == '__main__':
    # Disable analytics and telemetry
    import os
    os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
    demo.queue()
    # Launch on a fixed port for consistency
    demo.launch(
        server_name='0.0.0.0',  # Listen on all ports
        server_port=8000,  # Use consistent port
        share=False,  # Disable public sharing
        prevent_thread_lock=False,  # Keep the main thread alive
        show_error=True,
        debug=True
    )
    print("\nGradio app running at: http://localhost:8000")
    
    # Keep the app running
    demo.block_thread()