import gradio as gr
import requests
import random
import logging
from typing import Tuple
import easyocr
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
current_word = None
current_state = AppState.SETUP
current_session_id = None  # Add session ID tracking
current_word_id = None    # Add word ID tracking

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def get_word(group_id: str = "1") -> str:
    """Fetch a random word from the vocabulary."""
    global current_word, current_state, current_word_id
    try:
        # Fetch vocabulary from backend
        response = requests.get(f"http://localhost:5000/groups/{group_id}/words")
        if response.status_code != 200:
            return "Error: Failed to fetch words"
        
        words = response.json().get('words', [])
        if not words:
            return "Error: No words found in vocabulary"
        
        # Select random word
        word = random.choice(words)
        current_word = word['german']
        current_word_id = word['id']  # Store the word ID
        current_state = AppState.PRACTICE
        
        return current_word
    except Exception as e:
        logger.error(f"Error in get_word: {str(e)}")
        return f"Error: {str(e)}"

def submit_review(word_id: int, correct: bool, session_id: int) -> bool:
    """Submit the review result to the backend."""
    try:
        response = requests.post(
            f"http://localhost:5000/study_sessions/{session_id}/review",
            json={
                "word_id": word_id,
                "correct": correct
            }
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error submitting review: {str(e)}")
        return False

def create_session(study_activity_id: int = 1, group_id: int = 1) -> int:
    """Create a new study session."""
    try:
        response = requests.post(
            "http://localhost:5000/study_sessions",
            json={
                "study_activity_id": study_activity_id,
                "group_id": group_id
            }
        )
        if response.status_code == 201:
            return response.json().get("session_id")
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
    return None

def evaluate_handwriting(image_path) -> Tuple[str, str]:
    """Evaluate the handwritten text using OCR."""
    global current_word, current_state, current_word_id, current_session_id
    try:
        if not reader:
            return "Error", "OCR model not available"
        
        if not current_word:
            return "Error", "Please generate a new word first"
        
        if not image_path:
            return "Error", "No image provided"
        
        # Perform OCR on the image
        results = reader.readtext(image_path)
        
        if not results:
            return "Error", "No text detected in the image"
        
        # Get the text with highest confidence
        detected_text = max(results, key=lambda x: x[2])[1]
        similarity = calculate_similarity(detected_text, current_word)
        
        # Consider it correct if similarity is above 0.8 (80%)
        is_correct = similarity >= 0.8
        feedback = "Correct! " if is_correct else f"Incorrect  (You wrote: {detected_text})"
        
        # Submit the result to the backend if we have a session ID
        if current_session_id and current_word_id:
            if submit_review(current_word_id, is_correct, current_session_id):
                feedback += "\nResult saved successfully"
            else:
                feedback += "\nWarning: Could not save result"
        
        current_state = AppState.REVIEW
        return "Success", feedback
    
    except Exception as e:
        logger.error(f"Error in evaluate_handwriting: {str(e)}")
        return "Error", str(e)

def on_new_word():
    """Reset the interface for a new word."""
    global current_session_id
    
    # Create a new session if we don't have one
    if not current_session_id:
        current_session_id = create_session()
        if not current_session_id:
            return ["Error: Could not create session", None, gr.update(interactive=False), ""]
    
    word = get_word()
    return [word, None, gr.update(interactive=True), ""]

def on_submit(image):
    """Handle image submission and evaluation."""
    if not image:
        return [gr.update(interactive=True), "Error: No image provided"]
    
    status, feedback = evaluate_handwriting(image)
    return [gr.update(interactive=True), feedback]

# Initialize OCR reader
try:
    reader = easyocr.Reader(['de'])  # Initialize for German
    logger.info("OCR model loaded successfully")
except Exception as e:
    logger.error(f"Error loading OCR model: {str(e)}")
    reader = None

# Create Gradio interface
with gr.Blocks(title="German Word Writing Practice") as demo:
    gr.Markdown("# German Word Writing Practice")
    
    with gr.Row():
        with gr.Column():
            # Word display
            word_display = gr.Textbox(
                label="Write this word:",
                interactive=False
            )
            
            # Image upload
            image_input = gr.Image(
                label="Upload your handwriting",
                type="filepath",
                interactive=True
            )
            
            # Submit button
            submit_btn = gr.Button("Submit")
            
            # New word button
            new_word_btn = gr.Button("New Word")
            
            # Feedback display
            feedback_display = gr.Textbox(
                label="Feedback",
                interactive=False
            )
    
    # Set up event handlers
    new_word_btn.click(
        fn=on_new_word,
        outputs=[word_display, image_input, submit_btn, feedback_display]
    )
    
    submit_btn.click(
        fn=on_submit,
        inputs=[image_input],
        outputs=[submit_btn, feedback_display]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch()