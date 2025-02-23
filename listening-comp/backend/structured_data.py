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
    1: """Extract multiple choice questions from the first dialog (about Lutz) in this German conversation transcript.

            Format each question exactly like this:

            <question>
            Context:
            Person A: [Actual question from Dialog 1]
            Person B: [Actual answer from Dialog 1]
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
            - Focus on the first dialog 
            - Use actual phrases and answers from the conversation
            - Make other options plausible but clearly incorrect
            - Output questions one after another with no extra text between them
            """,
            
    2: """Extract multiple choice questions from the second dialog (about Johannes) in this German conversation transcript.

            Format each question exactly like this:

            <question>
            Context:
            Person A: [Actual question from Dialog 2]
            Person B: [Actual answer from Dialog 2]
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
            - Focus on the second dialog a
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
        """Structure the transcript into two sections based on the two dialogs"""
        results = {}
        
        # Find the approximate middle of the conversation where the second dialog starts
        # Looking for "gut jetzt habe ich ein paar fragen für dich" as the transition point
        dialog_parts = transcript.split("gut jetzt habe ich ein paar fragen für dich")
        
        if len(dialog_parts) > 1:
            # Process first dialog (about Lutz)
            result = self._invoke_bedrock(self.prompts[1], dialog_parts[0])
            if result:
                results[1] = result
            
            # Process second dialog (about Johannes)
            result = self._invoke_bedrock(self.prompts[2], dialog_parts[1])
            if result:
                results[2] = result
        else:
            # Fallback: just split in half if we can't find the transition phrase
            lines = transcript.split('\n')
            mid_point = len(lines) // 2
            
            # Process first dialog
            result = self._invoke_bedrock(self.prompts[1], '\n'.join(lines[:mid_point]))
            if result:
                results[1] = result
            
            # Process second dialog
            result = self._invoke_bedrock(self.prompts[2], '\n'.join(lines[mid_point:]))
            if result:
                results[2] = result
        
        return results

    def save_questions(self, structured_sections: Dict[int, str], base_filename: str):
        """Save each section to a separate file"""
        section_names = {
            1: "dialog1_lutz",
            2: "dialog2_johannes"
        }
        
        for section_num, content in structured_sections.items():
            section_name = section_names.get(section_num, f"section{section_num}")
            filename = f"{os.path.splitext(base_filename)[0]}_{section_name}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

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