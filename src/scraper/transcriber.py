import logging

import whisper


class Transcriber:
    """
    A class to transcribe audio files using the Whisper model.

    Attributes:
        audio_path (str): Path to the audio file.
        model (whisper.Model): Whisper model instance.
    """

    def __init__(self, audio_path, model=None):
        """
        Initialize the Transcriber.

        Args:
            audio_path (str): Path to the audio file.
            model (whisper.Model, optional): Whisper model instance. Defaults to None.
        """
        self.audio_path = audio_path
        self.model = whisper.load_model("small") if model is None else model

    def transcribe_audio(self, verbose=False):
        """
        Transcribe the audio file.

        Args:
            verbose (bool): Whether to enable verbose output.

        Returns:
            str: Transcribed text.
        """
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
