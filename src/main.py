import os
import logging
import argparse
import warnings
import instaloader
from scraper.downloader import InstagramDownloader
from scraper.transcriber import Transcriber
from scraper.recipe_generator import RecipeGenerator
from firebase.client import FirebaseClient

logging.basicConfig(level=logging.INFO)

# Suppress specific FutureWarning from torch.load
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="You are using `torch.load` with `weights_only=False`",
)


def get_audio(downloader, post_url, firebase_client, shortcode, audio_path, local=False):
    """
    Get the audio file for the Instagram post.

    Args:
        downloader (InstagramDownloader): Downloader instance.
        post_url (str): URL of the Instagram post.
        firebase_client (FirebaseClient): FirebaseClient instance.
        shortcode (str): Shortcode of the Instagram post.
        audio_path (str): Path to save the audio file.
        local (bool): Whether to save files locally or to Firebase.

    Returns:
        str: Caption of the Instagram post.
    """
    if local and os.path.exists(audio_path):
        logging.info(f"Audio for {shortcode} already exists locally.")
    else:
        try:
            firebase_client.download_file(f"audio/{shortcode}.mp3", audio_path)
            logging.info(f"Audio for {shortcode} downloaded from Firebase Storage.")
        except FileNotFoundError:
            logging.info(f"Audio for {shortcode} does not exist in Firebase Storage.")
            try:
                audio_path, caption = downloader.download_content(post_url)
                firebase_client.upload_file(audio_path, f"audio/{shortcode}.mp3")
                firebase_client.set_document(
                    "audio_metadata",
                    f"{shortcode}.mp3",
                    {"caption": caption, "audio_path": f"audio/{shortcode}.mp3"},
                )
                return caption
            except Exception as e:
                logging.error(f"Failed to download audio: {e}")
                raise e
    return firebase_client.get_document("audio_metadata", f"{shortcode}.mp3").get("caption", "")


def get_transcript(firebase_client, shortcode, audio_path, verbose):
    """
    Get the transcript for the audio file.

    Args:
        firebase_client (FirebaseClient): FirebaseClient instance.
        shortcode (str): Shortcode of the Instagram post.
        audio_path (str): Path to the audio file.
        verbose (bool): Whether to enable verbose output.

    Returns:
        str: Transcript of the audio file.
    """
    try:
        transcript = firebase_client.get_document(
            "transcripts", shortcode, local_path=f"transcripts/{shortcode}.txt"
        ).get("transcript", "")
        logging.info(f"Transcript for {shortcode} already exists.")
    except FileNotFoundError:
        logging.info(f"Transcript for {shortcode} does not exist.")
        logging.info("Transcribing audio...")
        transcriber = Transcriber(audio_path)
        transcript = transcriber.transcribe_audio(verbose)
        if not transcript:
            logging.error("Failed to transcribe audio.")
            raise ValueError("Failed to transcribe audio.")
        firebase_client.set_document("transcripts", shortcode, {"transcript": transcript})
    return transcript


def get_caption(downloader, shortcode):
    """
    Get the caption for the Instagram post.

    Args:
        downloader (InstagramDownloader): Downloader instance.
        shortcode (str): Shortcode of the Instagram post.

    Returns:
        str: Caption of the Instagram post.
    """
    logging.info("Fetching caption...")
    post = instaloader.Post.from_shortcode(downloader.loader.context, shortcode)
    return post.caption


def process_post(downloader, post_url, firebase_client, verbose=False, local=False):
    """
    Process an Instagram post to generate a recipe.

    Args:
        downloader (InstagramDownloader): Downloader instance.
        post_url (str): URL of the Instagram post.
        firebase_client (FirebaseClient): FirebaseClient instance.
        verbose (bool): Whether to enable verbose output.
        local (bool): Whether to save files locally or to Firebase.
    """
    shortcode = downloader._get_shortcode(post_url)
    audio_path = os.path.join("downloads", f"{shortcode}.mp3")
    recipe_path = os.path.join("recipes", f"recipe_{shortcode}.md")

    try:
        caption = get_audio(downloader, post_url, firebase_client, shortcode, audio_path, local)
    except Exception as e:
        logging.error(f"Error getting audio: {e}")
        return

    try:
        transcript = get_transcript(firebase_client, shortcode, audio_path, verbose)
    except ValueError as e:
        logging.error(f"Error getting transcript: {e}")
        return

    try:
        recipe = firebase_client.download_string(f"recipes/recipe_{shortcode}.md")
        logging.info(f"Recipe for {shortcode} already exists.")
        logging.info("Done!")
        return
    except FileNotFoundError:
        logging.info(f"Recipe for {shortcode} does not exist.")
    except Exception as e:
        logging.error(f"Error retrieving recipe: {e}")
        return

    if not caption:
        caption = get_caption(downloader, shortcode)

    logging.info("Generating recipe...")
    generator = RecipeGenerator(output_dir="recipes", local=local, firebase_client=firebase_client)
    try:
        recipe = generator.generate_recipe(transcript, caption)
        generator.save_recipe(recipe, shortcode)
    except ValueError as e:
        logging.error(f"Recipe generation failed: {e}")
        return

    if verbose or logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        logging.info(f"Generated recipe:\n{recipe}")

    logging.info("Done!")


def main():
    """
    Main function to parse arguments and process Instagram posts.
    """
    parser = argparse.ArgumentParser(
        description="Process Instagram post URLs to generate recipes."
    )
    parser.add_argument(
        "post_urls", nargs="+", help="Instagram post URL(s), separated by spaces"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--local", action="store_true", default=False, help="Save files locally instead of Firestore"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    firebase_client = FirebaseClient(local=args.local)
    downloader = InstagramDownloader(local=args.local)

    for post_url in args.post_urls:
        process_post(
            downloader, post_url, firebase_client, verbose=args.debug, local=args.local
        )


if __name__ == "__main__":
    main()
