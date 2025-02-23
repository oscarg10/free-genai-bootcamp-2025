import boto3
import json
import os
from typing import Dict, List, Tuple
import tempfile
from datetime import datetime

class AudioGenerator:
    def __init__(self):
        """Initialize the AudioGenerator with AWS clients"""
        self.bedrock = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.polly = boto3.client('polly')
        
        # Define SSML pauses
        self.short_pause = '<break time="0.5s"/>'
        self.medium_pause = '<break time="1s"/>'
        self.long_pause = '<break time="2s"/>'

    def generate_audio(self, question_data: Dict) -> str:
        """Generate audio for the entire question"""
        audio_parts = []
        current_section = None
        
        try:
            # Generate audio for context
            if 'Context' in question_data:
                context = question_data['Context'].strip()
                if context:
                    text = f'<speak>Kontext: {context}{self.medium_pause}</speak>'
                    audio = self.generate_audio_part(text, 'Daniel')
                    if audio:
                        audio_parts.append(audio)
            
            # Generate audio for dialog
            if 'Dialog' in question_data:
                dialog = question_data['Dialog']
                parts = dialog.split('Person ')
                
                for part in parts:
                    if not part.strip():
                        continue
                    
                    if part.startswith('A:'):
                        text = part[2:].strip()
                        if text:
                            ssml = f'<speak>{text}{self.short_pause}</speak>'
                            audio = self.generate_audio_part(ssml, 'Daniel')
                            if audio:
                                audio_parts.append(audio)
                    
                    elif part.startswith('B:'):
                        text = part[2:].strip()
                        if text:
                            ssml = f'<speak>{text}{self.short_pause}</speak>'
                            audio = self.generate_audio_part(ssml, 'Vicki')
                            if audio:
                                audio_parts.append(audio)
            
            # Generate audio for question
            if 'Question' in question_data:
                question = question_data['Question'].strip()
                if question:
                    text = f'<speak>{self.medium_pause}Frage: {question}{self.medium_pause}</speak>'
                    audio = self.generate_audio_part(text, 'Daniel')
                    if audio:
                        audio_parts.append(audio)
            
            # Generate audio for options
            if 'Options' in question_data:
                for i, option in enumerate(question_data['Options']):
                    text = f'<speak>Option {chr(65+i)}: {option}{self.short_pause}</speak>'
                    audio = self.generate_audio_part(text, 'Daniel')
                    if audio:
                        audio_parts.append(audio)
            
            # Combine all audio files
            if audio_parts:
                # Create output file
                output_file = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "frontend/static/audio",
                    f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                )
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                try:
                    # Combine audio files by concatenating binary data
                    with open(output_file, 'wb') as outfile:
                        for audio_file in audio_parts:
                            if os.path.exists(audio_file):
                                with open(audio_file, 'rb') as infile:
                                    outfile.write(infile.read())

                    # Clean up individual files
                    for audio_file in audio_parts:
                        try:
                            if os.path.exists(audio_file):
                                os.unlink(audio_file)
                        except Exception:
                            pass

                    return output_file

                except Exception as e:
                    print(f"Error combining audio files: {str(e)}")
                    if os.path.exists(output_file):
                        os.unlink(output_file)
                    return None
            
            return None
            
        except Exception as e:
            print(f"Error generating audio sequence: {str(e)}")
            return None

    def generate_audio_part(self, text: str, voice_name: str = 'Vicki') -> str:
        """Generate audio for a single part using Amazon Polly"""
        try:
            response = self.polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_name,
                Engine='neural',
                TextType='ssml',
                LanguageCode='de-DE'
            )
            
            if "AudioStream" in response:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(response['AudioStream'].read())
                    return temp_file.name
            
            return None
        except Exception as e:
            print(f"Error generating audio part: {str(e)}")
            return None