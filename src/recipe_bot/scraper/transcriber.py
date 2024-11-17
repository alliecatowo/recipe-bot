import whisper

import logging

model = whisper.load_model("small")


class Transcriber:
    def __init__(self, audio_path):
        self.audio_path = audio_path

    def transcribe_audio(self, verbose=False):
        try:
            response = model.transcribe(
                audio=self.audio_path, language="en", verbose=True, fp16=False
            )
            return response.get("text", "")
        except Exception as e:
            logging.error(f"Error during transcription: {e}")
            return ""
