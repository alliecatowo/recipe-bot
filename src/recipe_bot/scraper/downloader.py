import instaloader
import os
import requests
import logging
from pydub import AudioSegment
import firebase_admin
from firebase_admin import credentials, firestore, storage


class InstagramDownloader:
    def __init__(self, local=False):
        self.loader = instaloader.Instaloader()
        self.local = local
        self.firebase_app = None
        if not local:
            try:
                # Path to the service account key file
                service_account_path = os.path.join(
                    os.path.dirname(__file__), "../../../.private/firebasekey.json"
                )

                # Initialize Firebase Admin SDK with the service account key file
                if not firebase_admin._apps:
                    cred = credentials.Certificate(service_account_path)
                    self.firebase_app = firebase_admin.initialize_app(
                        cred,
                        {
                            "storageBucket": "ai-recipe-bot-d0b13.firebasestorage.app",
                            "projectId": "ai-recipe-bot-d0b13",
                        },
                    )
                self.db = firestore.client()
                self.bucket = storage.bucket()
                logging.info(
                    "Firebase initialized successfully with service account credentials."
                )
            except Exception as e:
                logging.error(f"Error initializing Firebase: {e}")
                raise

    def download_content(self, post_url, output_dir="downloads"):
        os.makedirs(output_dir, exist_ok=True)
        try:
            post = instaloader.Post.from_shortcode(
                self.loader.context, self._get_shortcode(post_url)
            )
            caption = post.caption
            video_url = post.video_url

            audio_path = os.path.join(
                output_dir, f"{self._get_shortcode(post_url)}.mp3"
            )
            if not os.path.exists(audio_path):
                video_path = os.path.join(
                    output_dir, f"{self._get_shortcode(post_url)}.mp4"
                )
                self._download_video(video_url, video_path)
                self._convert_to_audio(video_path, audio_path)

            if not self.local:
                self._upload_to_firebase(audio_path)

            return audio_path, caption
        except Exception as e:
            logging.error(f"Error downloading content: {e}")
            return None, None

    def _get_shortcode(self, post_url):
        return post_url.split("/")[-2]

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
            audio.export(audio_path, format="mp3", bitrate="192k")
            logging.info(f"Audio extracted to {audio_path}")
        except Exception as e:
            logging.error(f"Error converting video to audio: {e}")

    def _upload_to_firebase(self, audio_path):
        try:
            blob = self.bucket.blob(f"audio/{os.path.basename(audio_path)}")
            blob.upload_from_filename(audio_path)
            logging.info(
                f"Audio uploaded to Firebase Storage at audio/{os.path.basename(audio_path)}"
            )
        except Exception as e:
            logging.error(f"Error uploading audio to Firebase Storage: {e}")

    def file_exists_in_firebase(self, path):
        try:
            blob = self.bucket.blob(path)
            return blob.exists()
        except Exception as e:
            logging.error(f"Error checking file existence in Firebase: {e}")
            return False
