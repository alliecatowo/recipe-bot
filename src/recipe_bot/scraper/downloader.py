import instaloader
import os
import requests
import logging
from pydub import AudioSegment
import firebase_admin
from firebase_admin import credentials, firestore, storage


class InstagramDownloader:
    """
    A class to download Instagram posts and handle Firebase storage.

    Attributes:
        local (bool): Whether to save files locally or to Firebase.
        loader (instaloader.Instaloader): Instaloader instance for downloading posts.
        firebase_app (firebase_admin.App): Firebase app instance.
        db (firestore.Client): Firestore client.
        bucket (storage.Bucket): Firebase storage bucket.
    """

    def __init__(self, local=False):
        """
        Initialize the InstagramDownloader.

        Args:
            local (bool): Whether to save files locally or to Firebase.
        """
        self.loader = instaloader.Instaloader()
        self.local = local
        self.firebase_app = None
        if not local:
            try:
                service_account_path = os.path.join(
                    os.path.dirname(__file__), "../../../.private/firebasekey.json"
                )
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
        """
        Download content from an Instagram post.

        Args:
            post_url (str): URL of the Instagram post.
            output_dir (str): Directory to save the downloaded content.

        Returns:
            tuple: Path to the audio file and the post caption.
        """
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

    def _convert_to_audio(self, video_path, audio_path):
        """
        Convert video to audio.

        Args:
            video_path (str): Path to the video file.
            audio_path (str): Path to save the converted audio file.
        """
        try:
            audio = AudioSegment.from_file(video_path, format="mp4")
            audio.export(audio_path, format="mp3", bitrate="192k")
            logging.info(f"Audio extracted to {audio_path}")
        except Exception as e:
            logging.error(f"Error converting video to audio: {e}")

    def _upload_to_firebase(self, audio_path):
        """
        Upload audio file to Firebase Storage.

        Args:
            audio_path (str): Path to the audio file.
        """
        try:
            blob = self.bucket.blob(f"audio/{os.path.basename(audio_path)}")
            blob.upload_from_filename(audio_path)
            logging.info(
                f"Audio uploaded to Firebase Storage at audio/{os.path.basename(audio_path)}"
            )
        except Exception as e:
            logging.error(f"Error uploading audio to Firebase Storage: {e}")

    def file_exists_in_firebase(self, path):
        """
        Check if a file exists in Firebase Storage.

        Args:
            path (str): Path to the file in Firebase Storage.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            blob = self.bucket.blob(path)
            return blob.exists()
        except Exception as e:
            logging.error(f"Error checking file existence in Firebase: {e}")
            return False

    def transcript_exists_in_firestore(self, shortcode):
        """
        Check if a transcript exists in Firestore.

        Args:
            shortcode (str): Shortcode of the Instagram post.

        Returns:
            bool: True if the transcript exists, False otherwise.
        """
        try:
            doc_ref = self.db.collection("transcripts").document(shortcode)
            return doc_ref.get().exists
        except Exception as e:
            logging.error(f"Error checking transcript existence in Firestore: {e}")
            return False

    def recipe_exists_in_firestore(self, shortcode):
        """
        Check if a recipe exists in Firestore.

        Args:
            shortcode (str): Shortcode of the Instagram post.

        Returns:
            bool: True if the recipe exists, False otherwise.
        """
        try:
            doc_ref = self.db.collection("recipes").document(shortcode)
            return doc_ref.get().exists
        except Exception as e:
            logging.error(f"Error checking recipe existence in Firestore: {e}")
            return False

    def get_transcript_from_firestore(self, shortcode):
        """
        Retrieve a transcript from Firestore.

        Args:
            shortcode (str): Shortcode of the Instagram post.

        Returns:
            str: Transcript text.
        """
        try:
            doc_ref = self.db.collection("transcripts").document(shortcode)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("transcript", "")
            return ""
        except Exception as e:
            logging.error(f"Error retrieving transcript from Firestore: {e}")
            return ""

    def get_recipe_from_firestore(self, shortcode):
        """
        Retrieve a recipe from Firestore.

        Args:
            shortcode (str): Shortcode of the Instagram post.

        Returns:
            str: Recipe text.
        """
        try:
            doc_ref = self.db.collection("recipes").document(shortcode)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("recipe", "")
            return ""
        except Exception as e:
            logging.error(f"Error retrieving recipe from Firestore: {e}")
            return ""
