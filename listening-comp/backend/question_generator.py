import os
import json
import boto3
from typing import Dict, List, Optional
from backend.vector_store import QuestionVectorStore

class QuestionGenerator:
    def __init__(self):
        """Initialize Bedrock client and vector store"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.vector_store = QuestionVectorStore()
        self.model_id = "amazon.nova-lite-v1:0"

    def _invoke_bedrock(self, prompt: str) -> Optional[str]:
        """Invoke Bedrock with the given prompt"""
        try:
            messages = [{
                "role": "user",
                "content": [{
                    "text": prompt
                }]
            }]
            
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.7}
            )
            
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Error invoking Bedrock: {str(e)}")
            return None

    def generate_similar_question(self, section_num: int, topic: str) -> Dict:
        """Generate a new question similar to existing ones on a given topic"""
        # Get similar questions for context
        similar_questions = self.vector_store.search_similar_questions(section_num, topic, n_results=3)
        
        if not similar_questions:
            return None
        
        # Create context from similar questions
        context = "Here are some example German A1 listening questions:\n\n"
        for idx, q in enumerate(similar_questions, 1):
            context += f"Example {idx}:\n"
            
            if section_num in [1, 2]:  # Dialog-based questions
                context += f"Context: {q.get('Context', '')}\n"
                context += "Dialog:\n"
                context += f"Person A: {q.get('Dialog A', '')}\n"
                context += f"Person B: {q.get('Dialog B', '')}\n"
                if q.get('Follow-up A'):
                    context += f"Person A: {q.get('Follow-up A')}\n"
                if q.get('Follow-up B'):
                    context += f"Person B: {q.get('Follow-up B')}\n"
                context += f"\nQuestion: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Options:\n"
                    for i, opt in enumerate(['A', 'B', 'C', 'D']):
                        context += f"{opt}) {q['Options'][i]}\n"
            else:  # section 2
                context += f"Situation: {q.get('Situation', '')}\n"
                context += f"Question: {q.get('Question', '')}\n"
                if 'Options' in q:
                    context += "Options:\n"
                    for i, opt in enumerate(q['Options'], 1):
                        context += f"{i}. {opt}\n"
            
            context += "\n\n"
        
        # Create prompt for generating new question
        prompt = f"""Based on these example German A1 level questions, create a new multiple choice question following the same format.

IMPORTANT: Wrap your response in <question> tags and follow this EXACT format:
<question>
Context: [brief setting for the conversation, e.g. "Im Restaurant" or "Im Supermarkt"]
Dialog:
Person A: [a clear question in German, e.g. "Was möchten Sie bestellen?"]
Person B: [a complete answer in German, e.g. "Ich möchte eine Suppe und einen Salat bestellen."]

Question: [question about the dialog]
Options:
A) [correct answer that matches Person B's response]
B) [plausible but incorrect answer]
C) [plausible but incorrect answer]
D) [plausible but incorrect answer]
</question>

Rules:
1. Context should be a simple location or situation, NOT include question numbers
2. Person A must ask a clear question
3. Person B must give a complete answer
4. The correct answer (A) must match Person B's response
5. Use simple A1 level German
6. Make all options grammatically similar

Topic to focus on: {topic}

Example questions for reference:
{context}

Generate a new question following the EXACT same format, but make sure to:
1. Wrap it in <question> tags
2. Use different content than the examples
3. Keep all text in German
4. Make the options plausible but clearly incorrect
5. Include all sections: Context, Dialog, Question, Options
"""

        # Generate new question
        response = self._invoke_bedrock(prompt)
        if not response:
            return None

        # Try XML tag parsing first
        questions_raw = response.split("<question>")
        if len(questions_raw) >= 2:
            question_raw = questions_raw[1].split("</question>")[0].strip()
            print("DEBUG - Found question with XML tags")
        else:
            # Fallback: try to parse without XML tags
            print("DEBUG - No XML tags found, trying fallback parsing")
            # Skip any leading text before the first section
            lines = response.split('\n')
            start_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith(("Context:", "**Context:**")):
                    start_idx = i
                    break
            
            if start_idx == -1:
                print("DEBUG - Could not find start of question")
                return None
                
            question_raw = '\n'.join(lines[start_idx:])
        
        print("DEBUG - Processing question:", question_raw)
        lines = question_raw.split('\n')
        question = {}
        current_key = None
        current_value = []
        options = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            print("DEBUG - Processing line:", line)
            
            # Skip non-content lines
            if any(line.startswith(x) for x in [
                "Sure,", "Example", "Here's", "In this", "---", "Correct Answer:"
            ]):
                continue
            
            # Handle both markdown and non-markdown headers
            if line.startswith(("Context:", "**Context:**")):
                if current_key:
                    question[current_key] = ' '.join(current_value).strip()
                    print(f"DEBUG - Saved {current_key}: {question[current_key]}")
                current_key = 'Context'
                current_value = [line.replace("Context:", "").replace("**", "").strip()]
            elif line.startswith("Person A:"):
                if current_key != 'Dialog':
                    if current_key:
                        question[current_key] = ' '.join(current_value).strip()
                    current_key = 'Dialog'
                    current_value = []
                current_value.append(line)
            elif line.startswith("Person B:"):
                if current_key != 'Dialog':
                    if current_key:
                        question[current_key] = ' '.join(current_value).strip()
                    current_key = 'Dialog'
                    current_value = []
                current_value.append(line)
            elif line.startswith(("Question:", "**Question:**")):
                if current_key:
                    question[current_key] = ' '.join(current_value).strip()
                    print(f"DEBUG - Saved {current_key}: {question[current_key]}")
                current_key = 'Question'
                current_value = [line.replace("Question:", "").replace("**", "").strip()]
            elif line.startswith(("Options:", "**Options:**", "Options [use actual")):
                if current_key:
                    question[current_key] = ' '.join(current_value).strip()
                    print(f"DEBUG - Saved {current_key}: {question[current_key]}")
                current_key = 'Options'
                current_value = []
            elif line.startswith(("A)", "B)", "C)", "D)")):
                if current_key == 'Options':
                    # Store the option and its letter
                    options.append((line[0], line[3:].strip()))
                    print("DEBUG - Added option:", line[0], "-", line[3:].strip())
            elif current_key and current_key != 'Options':
                current_value.append(line)
        
        if current_key:
            if current_key == 'Options':
                # Find the correct answer (it's in the dialog)
                dialog_text = ' '.join(question.get('Dialog', [])).lower()
                correct_option = None
                for letter, text in options:
                    text_lower = text.lower()
                    if text_lower in dialog_text:
                        correct_option = (letter, text)
                        break
                
                if not correct_option:
                    # If no exact match found, use the first option as correct
                    correct_option = options[0] if options else None
                
                if correct_option:
                    # Reorder options to make the correct one first
                    other_options = [opt for opt in options if opt != correct_option]
                    options = [correct_option] + other_options
                    
                # Store final ordered options
                question['Options'] = [text for _, text in options]
            else:
                question[current_key] = '\n'.join(current_value).strip()
                print(f"DEBUG - Final save of {current_key}: {question[current_key]}")
        
        # Validate required fields
        required_fields = ['Context', 'Dialog', 'Question', 'Options']
        missing_fields = [field for field in required_fields if field not in question]
        if missing_fields:
            print("DEBUG - Missing required fields:", missing_fields)
            return None

        # Validate dialog content
        dialog = question.get('Dialog', '')
        
        # Check for empty or template dialog
        if dialog.strip() in ['', 'Person A: Person B:', 'Dialog:']:
            print("DEBUG - Empty or invalid dialog")
            return None
        
        # Split dialog into parts
        dialog_parts = dialog.split('Person ')
        person_a_content = ''
        person_b_content = ''
        
        for part in dialog_parts:
            if part.startswith('A:'):
                person_a_content = part[2:].strip()
            elif part.startswith('B:'):
                person_b_content = part[2:].strip()
        
        # Validate both speakers have content
        if not person_a_content or not person_b_content:
            print("DEBUG - Missing content for one or both speakers")
            return None
            
        # Validate Person A asks a question (contains ?)
        if '?' not in person_a_content:
            print("DEBUG - Person A's dialog doesn't contain a question")
            return None
            
        # Clean up context (remove any "Person A: Nummer X" prefix)
        context = question.get('Context', '')
        if 'Person A: Nummer' in context:
            context = context.split('Dialog:')[0].split(', ')[1].strip()
            question['Context'] = context
        
        # Validate options
        if not question.get('Options') or len(question['Options']) != 4:
            print("DEBUG - Missing or invalid options")
            return None
            
        print("DEBUG - Final question object:", json.dumps(question, indent=2))
        
        return question

    def get_feedback(self, question: Dict, user_answer: str) -> Dict:
        """Generate feedback for a user's answer in simple German"""
        # Get the correct answer (first option is always correct)
        correct_answer = question['Options'][0]
        
        # Convert letter answer (A, B, C, D) to index (0, 1, 2, 3)
        user_answer_idx = ord(user_answer) - ord('A')
        user_answer_text = question['Options'][user_answer_idx]
        
        # Check if answer is correct
        is_correct = user_answer_idx == 0  # A is always correct
        
        prompt = f"""Provide feedback in simple German (A1 level) for this answer.
        
        Question: {question['Question']}
        Correct Answer: {correct_answer}
        User's Answer: {user_answer_text}
        
        Rules:
        1. Use very simple German (A1 level)
        2. Be encouraging and friendly
        3. If correct, give praise
        4. If incorrect, gently explain the right answer
        5. Keep the response to 1-2 short sentences
        """
        
        response = self._invoke_bedrock(prompt)
        message = response if response else "Keine Rückmeldung verfügbar."
        
        return {
            "correct": is_correct,
            "message": message,
            "user_answer": user_answer_text,
            "correct_answer": correct_answer
        }