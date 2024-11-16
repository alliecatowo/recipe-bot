import requests
from config.config import WHISPER_API_URL, OPENAI_API_KEY


class Transcriber:
    def __init__(self, audio_path):
        self.audio_path = audio_path

    def transcribe_audio(self):
        try:
            with open(self.audio_path, "rb") as audio_file:
                response = requests.post(
                    WHISPER_API_URL,
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    files={"file": audio_file},
                    data={"model": "whisper-1"},
                )
            return response.json().get("text", "")
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""
