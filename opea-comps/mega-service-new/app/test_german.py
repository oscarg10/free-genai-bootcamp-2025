import requests
import json
import time

def wait_for_services():
    """Wait for services to be ready"""
    print("Waiting for services to start...")
    services = [
        ("Megaservice", "http://localhost:8888/james-is-great"),
        ("Ollama", "http://localhost:11434/api/generate"),
        ("TTS", "http://localhost:9088/tts")
    ]
    
    for name, url in services:
        while True:
            try:
                requests.get(url)
                print(f"{name} is ready!")
                break
            except:
                print(f"Waiting for {name}...")
                time.sleep(5)

def generate_german_text():
    llm_url = "http://localhost:8888/james-is-great"
    request_data = {
        "model": "llama2:7b",
        "messages": [
            {
                "role": "user",
                "content": "Übersetze den folgenden Satz ins Deutsche: 'Hello! Today is a beautiful day and I am happy to be here.'"
            }
        ]
    }
    
    print("Generating German text...")
    try:
        response = requests.post(llm_url, json=request_data)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            print(f"Error from server: {response.text}")
            return None
            
        result = response.json()
        if result and 'choices' in result and len(result['choices']) > 0:
            text = result['choices'][0]['message']['content']
            print(f"Generated text: {text}")
            return text
        return None
    except Exception as e:
        print(f"Error making request: {str(e)}")
        return None

def text_to_speech(german_text):
    if not german_text:
        print("No text to convert to speech")
        return
        
    tts_url = "http://localhost:9088/tts"
    request_data = {
        "refer_wav_path": "/audio/oscar-ref-10s.wav",
        "prompt_text": "Hallo, wie geht es dir?",
        "prompt_language": "de",
        "text": german_text,
        "text_language": "de"
    }
    
    print("\nConverting to speech...")
    try:
        response = requests.post(tts_url, json=request_data)
        if response.status_code == 200:
            with open("test_german.wav", "wb") as f:
                f.write(response.content)
            print("Audio saved as 'test_german.wav'")
        else:
            print(f"Error from TTS server: {response.text}")
    except Exception as e:
        print(f"Error in TTS conversion: {str(e)}")

if __name__ == "__main__":
    try:
        wait_for_services()
        german_text = generate_german_text()
        if german_text:
            text_to_speech(german_text)
    except Exception as e:
        print(f"Error: {str(e)}")