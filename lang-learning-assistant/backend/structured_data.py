from typing import Optional, Dict
import boto3
import os
import json

# Model ID
MODEL_ID = "amazon.nova-micro-v1:0"
# MODEL_ID = "amazon.nova-lite-v1:0"

class TranscriptStructurer:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.transcript_dir = os.path.join(self.base_dir, "data", "transcripts")
        self.questions_dir = os.path.join(self.base_dir, "data", "questions")
        
        # Ensure directories exist
        os.makedirs(self.transcript_dir, exist_ok=True)
        os.makedirs(self.questions_dir, exist_ok=True)

        self.prompts = {
    1: """Extract multiple choice questions from this German conversation transcript. Focus on questions about personal information and basic facts.

            Format each question exactly like this:

            <question>
            Context:
            Person A: [Actual question from the conversation]
            Person B: [Actual answer from the conversation]
            [Include any relevant follow-up exchanges]
            
            Question: [The actual question in German]
            
            Options [use actual information from the conversation when possible]:
            A) [First option in German]
            B) [Second option in German]
            C) [Third option in German]
            D) [Fourth option in German]
            </question>

            Rules:
            - Show the context as a dialogue between speakers
            - Include the actual question and answer exchange from the conversation
            - Keep all text in German
            - Focus on factual information (names, places, hobbies, etc.)
            - Use actual phrases and answers from the conversation
            - Make other options plausible but clearly incorrect
            - Output questions one after another with no extra text between them
            """,
            
    2: """Extract multiple choice questions about hobbies and activities from this German conversation transcript.

            Format each question exactly like this:

            <question>
            Context:
            Person A: [Actual question about hobbies/activities]
            Person B: [Actual answer]
            [Include any relevant follow-up exchanges]
            
            Question: [The actual question in German]
            
            Options [use actual information from the conversation when possible]:
            A) [First option in German]
            B) [Second option in German]
            C) [Third option in German]
            D) [Fourth option in German]
            </question>

            Rules:
            - Show the context as a dialogue between speakers
            - Include the actual question and answer exchange from the conversation
            - Keep all text in German
            - Focus on hobbies, sports, and frequency of activities
            - Use actual phrases and answers from the conversation
            - Make other options plausible but clearly incorrect
            - Output questions one after another with no extra text between them
            """,
            
    3: """Extract multiple choice questions about daily life and routines from this German conversation transcript.

            Format each question exactly like this:

            <question>
            Context:
            Person A: [Actual question about daily life]
            Person B: [Actual answer]
            [Include any relevant follow-up exchanges]
            
            Question: [The actual question in German]
            
            Options [use actual information from the conversation when possible]:
            A) [First option in German]
            B) [Second option in German]
            C) [Third option in German]
            D) [Fourth option in German]
            </question>

            Rules:
            - Show the context as a dialogue between speakers
            - Include the actual question and answer exchange from the conversation
            - Keep all text in German
            - Focus on daily activities and routines
            - Use actual phrases and answers from the conversation
            - Make other options plausible but clearly incorrect
            - Output questions one after another with no extra text between them
            """
    }


    def _invoke_bedrock(self, prompt: str, transcript: str) -> Optional[str]:
        """Make a single call to Bedrock with the given prompt"""
        full_prompt = f"{prompt}\n\nHere's the transcript:\n{transcript}"
        
        messages = [{
            "role": "user",
            "content": [{"text": full_prompt}]
        }]

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0}
            )
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            print(f"Error invoking Bedrock: {str(e)}")
            return None

    def structure_transcript(self, transcript: str) -> Dict[int, str]:
        """Structure the transcript into three sections using separate prompts"""
        results = {}
        # Skipping section 1 for now
        for section_num in range(1, 4):
            result = self._invoke_bedrock(self.prompts[section_num], transcript)
            if result:
                results[section_num] = result
        return results

    def save_questions(self, structured_sections: Dict[int, str], base_filename: str) -> bool:
        """Save each section to a separate file"""
        try:
            # Create questions directory if it doesn't exist
            os.makedirs(os.path.dirname(base_filename), exist_ok=True)
            
            # Save each section
            for section_num, content in structured_sections.items():
                filename = f"{os.path.splitext(base_filename)[0]}_section{section_num}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True
        except Exception as e:
            print(f"Error saving questions: {str(e)}")
            return False

    def load_transcript(self, filename: str) -> Optional[str]:
        """Load transcript from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None

if __name__ == "__main__":
    structurer = TranscriptStructurer()
    transcript_file = os.path.join(structurer.transcript_dir, "tlYgH1pK4rQ.txt")
    transcript = structurer.load_transcript(transcript_file)
    if transcript:
        structured_sections = structurer.structure_transcript(transcript)
        structurer.save_questions(structured_sections, os.path.join(structurer.questions_dir, "tlYgH1pK4rQ.txt"))
        
        # Pretty print the structured sections
        print("\nStructured Questions by Section:")
        print("=" * 50)
        for section_num, questions in structured_sections.items():
            print(f"\nSection {section_num}:")
            print("-" * 20)
            # Split questions by the <question> tag and filter out empty strings
            individual_questions = [q.strip() for q in questions.split("<question>") if q.strip()]
            for i, question in enumerate(individual_questions, 1):
                # Clean up the closing tag and extra newlines
                question = question.replace("</question>", "").strip()
                print(f"\nQuestion {i}:")
                print(question)
                print("-" * 20)