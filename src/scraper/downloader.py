import logging
import os

import instaloader
import requests
from pydub import AudioSegment


class InstagramDownloader:
    """
    A class to download Instagram posts and handle Firebase storage.

    Attributes:
        local (bool): Whether to save files locally or to Firebase.
        loader (instaloader.Instaloader): Instaloader instance for downloading posts.
    """

    def __init__(self, local=False):
        """
        Initialize the InstagramDownloader.

        Args:
            local (bool): Whether to save files locally or to Firebase.
        """
        self.loader = instaloader.Instaloader()
        self.local = local
        if not local:
            logging.info("Firebase initialized successfully.")

    def download_content(self, post_url, output_dir="downloads"):
        """
        Download content from an Instagram post.

        Args:
            post_url (str): URL of the Instagram post.
            output_dir (str): Directory to save the downloaded content.

        Returns:
            tuple: Path to the audio file and the post caption.

        Raises:
            Exception: If there is an error during download.
        """
        os.makedirs(output_dir, exist_ok=True)
        try:
            post = instaloader.Post.from_shortcode(
                self.loader.context, self._get_shortcode(post_url)
            )
            caption = post.caption
            video_url = post.video_url

            audio_path = os.path.join(output_dir, f"{self._get_shortcode(post_url)}.mp3")
            if not os.path.exists(audio_path):
                video_path = os.path.join(output_dir, f"{self._get_shortcode(post_url)}.mp4")
                self._download_video(video_url, video_path)
                self._convert_to_audio(video_path, audio_path)

            return audio_path, caption
        except Exception as e:
            logging.error(f"Error downloading content: {e}")
            raise e

    def _get_shortcode(self, post_url):
        """
        Extract the shortcode from the post URL.

        Args:
            post_url (str): URL of the Instagram post.

        Returns:
            str: Shortcode of the post.
        """
        return post_url.split("/")[-2]

    def _download_video(self, video_url, output_path):
        """
        Download video from the given URL.

        Args:
            video_url (str): URL of the video.
            output_path (str): Path to save the downloaded video.

        Raises:
            Exception: If there is an error during download.
        """
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
            raise e

    def _convert_to_audio(self, video_path, audio_path):
        """
        Convert video to audio.

        Args:
            video_path (str): Path to the video file.
            audio_path (str): Path to save the converted audio file.

        Raises:
            Exception: If there is an error during conversion.
        """
        try:
            audio = AudioSegment.from_file(video_path, format="mp4")
            audio.export(audio_path, format="mp3", bitrate="192k")
            logging.info(f"Audio extracted to {audio_path}")
        except Exception as e:
            logging.error(f"Error converting video to audio: {e}")
            raise e
