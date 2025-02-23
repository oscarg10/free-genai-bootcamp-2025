import streamlit as st
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.question_generator import QuestionGenerator

# Page config
st.set_page_config(
    page_title="German A1 Listening Practice",
    page_icon="🎧",
    layout="wide"
)

def load_stored_questions():
    """Load previously stored questions from JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend/data/stored_questions.json"
    )
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_question(question, practice_type, topic):
    """Save a generated question to JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend/data/stored_questions.json"
    )
    
    # Load existing questions
    stored_questions = load_stored_questions()
    
    # Create a unique ID for the question using timestamp
    question_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Add metadata
    question_data = {
        **question,  # Include all question data directly
        "practice_type": practice_type,
        "topic": topic,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add to stored questions
    stored_questions[question_id] = question_data
    
    # Save back to file
    os.makedirs(os.path.dirname(questions_file), exist_ok=True)
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(stored_questions, f, ensure_ascii=False, indent=2)

def cleanup_feedback_state():
    """Reset feedback-related session state variables"""
    if 'show_feedback' in st.session_state:
        del st.session_state.show_feedback

def generate_new_question():
    """Generate a new question and reset feedback state"""
    cleanup_feedback_state()
    try:
        # Generate new question based on current practice type
        if st.session_state.current_practice_type == "Dialogue Practice":
            print("DEBUG - Generating new question")
            print("DEBUG - Practice type:", st.session_state.current_practice_type)
            print("DEBUG - Topic:", st.session_state.current_topic)
            print("DEBUG - Section number:", 2)
            
            question = st.session_state.question_generator.generate_similar_question(
                2,
                st.session_state.current_topic
            )
            
            if question:
                print("DEBUG - Generated question:", json.dumps(question, indent=2))
                st.session_state.current_question = question
                print("DEBUG - Question saved to session state")
                # Save the generated question
                save_question(question, st.session_state.current_practice_type, st.session_state.current_topic)
            else:
                st.error("Failed to generate a new question. Please try again.")
    except Exception as e:
        print("DEBUG - Error generating question:", str(e))
        st.error("Error generating new question. Please try again.")

def render_interactive_stage():
    """Render the interactive learning stage"""
    # Initialize session state
    if 'question_generator' not in st.session_state:
        print("DEBUG - Initializing question generator")
        st.session_state.question_generator = QuestionGenerator()
    
    if 'current_question' not in st.session_state:
        print("DEBUG - Initializing current_question")
        st.session_state.current_question = None
    
    if 'current_practice_type' not in st.session_state:
        print("DEBUG - Initializing current_practice_type")
        st.session_state.current_practice_type = None
    
    if 'current_topic' not in st.session_state:
        print("DEBUG - Initializing current_topic")
        st.session_state.current_topic = None
    
    if 'feedback' not in st.session_state:
        print("DEBUG - Initializing feedback")
        st.session_state.feedback = None

    st.title("German A1 Listening Practice")
    st.write("Practice your German listening skills with interactive exercises!")

    # Load stored questions for sidebar
    stored_questions = load_stored_questions()
    
    # Create sidebar
    with st.sidebar:
        st.header("Saved Questions")
        if stored_questions:
            for qid, qdata in stored_questions.items():
                # Create a button for each question
                button_label = f"{qdata['practice_type']} - {qdata['topic']}\n{qdata['created_at']}"
                if st.button(button_label, key=qid):
                    # Remove metadata fields to get just the question data
                    question_data = {k: v for k, v in qdata.items() 
                                   if k not in ['practice_type', 'topic', 'created_at']}
                    st.session_state.current_question = question_data
                    st.session_state.current_practice_type = qdata['practice_type']
                    st.session_state.current_topic = qdata['topic']
                    st.session_state.feedback = None
                    st.rerun()
        else:
            st.info("No saved questions yet. Generate some questions to see them here!")

    # Practice type selection
    practice_type = st.selectbox(
        "Select Practice Type",
        ["Dialogue Practice", "Phrase Matching"]
    )

    if practice_type != st.session_state.get('current_practice_type'):
        cleanup_feedback_state()
        st.session_state.current_practice_type = practice_type
    
    # Topic selection
    topics = {
        "Dialogue Practice": ["Daily Conversation", "Shopping", "Restaurant", "Travel", "School/Work"],
        "Phrase Matching": ["Announcements", "Instructions", "Weather Reports", "News Updates"]
    }

    topic = st.selectbox(
        "Select Topic",
        topics[practice_type]
    )

    if topic != st.session_state.get('current_topic'):
        cleanup_feedback_state()
        st.session_state.current_topic = topic
    
    # Generate new question button
    if st.button("Generate New Question"):
        generate_new_question()

    # Print current state for debugging
    print("\nDEBUG - Current session state:")
    print("DEBUG - current_question:", json.dumps(st.session_state.current_question, indent=2) if st.session_state.current_question else None)
    print("DEBUG - current_practice_type:", st.session_state.current_practice_type)
    print("DEBUG - current_topic:", st.session_state.current_topic)

    # Display the current question if we have one
    if st.session_state.current_question:
        st.subheader("Practice Scenario")
        print("\nDEBUG - Displaying question")
        print("DEBUG - Question data:", json.dumps(st.session_state.current_question, indent=2))

        try:
            # Display question components based on practice type
            if st.session_state.current_practice_type == "Dialogue Practice":
                # Display Context
                if 'Context' in st.session_state.current_question:
                    context = st.session_state.current_question['Context'].strip()
                    st.markdown("**Context:**")
                    st.write(context)
                
                # Display Dialog
                if 'Dialog' in st.session_state.current_question:
                    dialog = st.session_state.current_question['Dialog']
                    st.markdown("**Dialog:**")
                    # Split by "Person" to separate dialog lines
                    dialog_parts = dialog.split("Person ")
                    for part in dialog_parts:
                        if part.strip():  # Skip empty parts
                            # Add "Person" back and display
                            line = f"Person {part.strip()}"
                            st.write(line)

            # Create columns for answer input and feedback
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Format options with letters and content
                if 'Options' in st.session_state.current_question:
                    options = st.session_state.current_question['Options']
                    formatted_options = [f"{chr(65+i)}) {option}" for i, option in enumerate(options)]
                    
                    # Display question
                    if 'Question' in st.session_state.current_question:
                        st.markdown("**Question:**")
                        st.write(st.session_state.current_question['Question'])
                    
                    # Answer selection with formatted options
                    selected_option = st.radio(
                        "Select your answer:",
                        formatted_options,
                        key="answer_selection"
                    )
                    
                    # Extract letter from selected option for feedback
                    selected_answer = selected_option[0] if selected_option else None
                
                # Check answer button with session state to maintain feedback
                if 'show_feedback' not in st.session_state:
                    st.session_state.show_feedback = False
                
                if st.button("Check Answer") or st.session_state.show_feedback:
                    st.session_state.show_feedback = True
                    if selected_answer:
                        feedback = st.session_state.question_generator.get_feedback(
                            st.session_state.current_question,
                            selected_answer
                        )
                        if feedback['correct']:
                            st.success(f"✓ Richtig! {feedback['message']}")
                        else:
                            st.error(f"✗ {feedback['message']}")
        except Exception as e:
            print("DEBUG - Error displaying question:", str(e))
            st.error("Error displaying question components. Please try generating a new question.")
    else:
        st.info("Click 'Generate New Question' to start practicing!")

def main():
    render_interactive_stage()

if __name__ == "__main__":
    main()