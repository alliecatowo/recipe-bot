import whisper
import logging


class Transcriber:
    def __init__(self, audio_path, model=None):
        self.audio_path = audio_path
        self.model = whisper.load_model("small") if model is None else model

    def transcribe_audio(self, verbose=False):
        try:
            response = self.model.transcribe(
                audio=self.audio_path,
                language="en",
                verbose=verbose,
                fp16=False,
            )
            return response.get("text", "")
        except Exception as e:
            logging.error(f"Error during transcription: {e}")
            return ""
