import instaloader
import os
import requests
import logging
from pydub import AudioSegment

class InstagramDownloader:
    def __init__(self, post_url):
        self.post_url = post_url
        self.loader = instaloader.Instaloader()

    def download_content(self, output_dir="downloads"):
        os.makedirs(output_dir, exist_ok=True)
        try:
            post = instaloader.Post.from_shortcode(
                self.loader.context, self._get_shortcode()
            )
            caption = post.caption
            video_url = post.video_url

            audio_path = os.path.join(output_dir, f"{self._get_shortcode()}.wav")
            if not os.path.exists(audio_path):
                video_path = os.path.join(output_dir, f"{self._get_shortcode()}.mp4")
                self._download_video(video_url, video_path)
                self._convert_to_audio(video_path, audio_path)
                os.remove(video_path)

            return audio_path, caption
        except Exception as e:
            logging.error(f"Error downloading content: {e}")
            return None, None

    def _get_shortcode(self):
        return self.post_url.split("/")[-2]

    def _download_video(self, video_url, output_path):
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            with open(output_path, "wb") as video_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        video_file.write(chunk)
            logging.info(f"Video successfully downloaded to {output_path}")
        except requests.RequestException as e:
            logging.error(f"Error downloading video: {e}")

    def _convert_to_audio(self, video_path, audio_path):
        try:
            audio = AudioSegment.from_file(video_path, format="mp4")
            audio.export(audio_path, format="wav")
            logging.info(f"Audio extracted to {audio_path}")
        except Exception as e:
            logging.error(f"Error converting video to audio: {e}")
