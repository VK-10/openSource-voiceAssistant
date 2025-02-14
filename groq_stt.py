import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_WHISPER_KEY = os.getenv("GROQ_WHISPER_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

audio = "kokoro-voice-1.wav"

headers = {
    "Authorization" : f"Bearer {GROQ_WHISPER_KEY}",
    "Accept": "application/json"
}

try:
    with open(audio, "rb") as audio_file:
        files = {
            "file": (os.path.basename(audio), audio_file, "audio/wav")
        }
        data = {
            "model" : "whisper-large-v3"
        }
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            files=files,
            data = data
        )
        
        if response.status_code == 200:
            transcription = response.json()["text"]
            print("transcription :" ,transcription)
        else:
            print("Error in WhisperX transcription: ", response.text)
except Exception as e:
    print("Exception during WhisperX transcription: ", e)
        