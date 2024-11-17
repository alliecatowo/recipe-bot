import whisper

from config.config import OPENAI_API_KEY
from pydub import AudioSegment
import os


model = whisper.load_model("small")


class Transcriber:
    def __init__(self, video_path):
        self.video_path = video_path
        self.audio_path = self.extract_audio()

    def extract_audio(self):
        audio_path = self.video_path.replace(".mp4", ".wav")
        # Use pydub to extract audio
        audio = AudioSegment.from_file(self.video_path, format="mp4")
        audio.export(audio_path, format="wav")
        return audio_path

    def transcribe_audio(self):
        try:
            with open(self.audio_path, "rb") as audio_file:
                response = model.transcribe(
                    audio=self.audio_path, language="en", verbose=True
                )
            return response.get("text", "")
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""
        finally:
            # Clean up the extracted audio file
            if os.path.exists(self.audio_path):
                os.remove(self.audio_path)
