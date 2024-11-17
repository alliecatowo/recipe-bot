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

    transcript = ""
    caption = ""

    if local:
        if os.path.exists(audio_path):
            logging.info(f"Audio for {shortcode} already exists locally.")
        if os.path.exists(recipe_path):
            logging.info(f"Recipe for {shortcode} already exists locally.")
            return
    else:
        if firebase_client.file_exists(f"audio/{shortcode}.mp3"):
            logging.info(f"Audio for {shortcode} already exists in Firebase.")
        if firebase_client.document_exists("transcripts", shortcode):
            logging.info(f"Transcript for {shortcode} already exists in Firestore.")
            transcript = firebase_client.get_document("transcripts", shortcode).get(
                "transcript", ""
            )
        if firebase_client.file_exists(f"recipes/recipe_{shortcode}.md"):
            logging.info(f"Recipe for {shortcode} already exists in Firebase Storage.")
            recipe = firebase_client.download_string(f"recipes/recipe_{shortcode}.md")
            if verbose or logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                logging.info(f"Generated recipe:\n{recipe}")
            logging.info("Done!")
            return

    if not os.path.exists(audio_path):
        logging.info("Downloading content...")
        audio_path, caption = downloader.download_content(post_url)
        if not os.path.exists(audio_path):
            logging.error(f"Failed to download audio: {audio_path}")
            return

    if not transcript:
        logging.info("Transcribing audio...")
        transcriber = Transcriber(audio_path)
        transcript = transcriber.transcribe_audio(verbose)
        if not transcript:
            logging.error("Failed to transcribe audio.")
            return

        if not local:
            firebase_client.set_document(
                "transcripts", shortcode, {"transcript": transcript}
            )

    if not caption:
        logging.info("Fetching caption...")
        post = instaloader.Post.from_shortcode(downloader.loader.context, shortcode)
        caption = post.caption

    logging.info("Generating recipe...")
    generator = RecipeGenerator(
        output_dir="recipes", local=local, firebase_client=firebase_client
    )
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
        "--local", action="store_true", help="Save files locally instead of Firestore"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    firebase_client = FirebaseClient()
    downloader = InstagramDownloader(local=args.local)

    for post_url in args.post_urls:
        process_post(
            downloader, post_url, firebase_client, verbose=args.debug, local=args.local
        )


if __name__ == "__main__":
    main()
