import argparse
import logging
import os
import uuid
import warnings

import instaloader

from firebase.client import FirebaseClient
from models.cookbook import Cookbook
from models.recipe import Recipe
from models.user import User
from scraper.downloader import InstagramDownloader
from scraper.recipe_generator import RecipeGenerator
from scraper.transcriber import Transcriber

logging.basicConfig(level=logging.INFO)

# Suppress specific FutureWarning from torch.load
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="You are using `torch.load` with `weights_only=False`",
)


def get_audio(
    downloader, post_url, firebase_client, shortcode, audio_path, local=False
):
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
    return firebase_client.get_document("audio_metadata", f"{shortcode}.mp3").get(
        "caption", ""
    )


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
        firebase_client.set_document(
            "transcripts", shortcode, {"transcript": transcript}
        )
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


def process_post(
    downloader,
    post_url,
    user,
    cookbook,
    generator,
    firebase_client,
    verbose=False,
    local=False,
):
    """
    Process an Instagram post to generate a recipe.

    Args:
        downloader (InstagramDownloader): Downloader instance.
        post_url (str): URL of the Instagram post.
        user (User): User instance.
        cookbook (Cookbook): Cookbook instance.
        generator (RecipeGenerator): RecipeGenerator instance.
        firebase_client (FirebaseClient): FirebaseClient instance.
        verbose (bool): Whether to enable verbose output.
        local (bool): Whether to save files locally or to Firebase.
    """
    shortcode = downloader._get_shortcode(post_url)
    audio_path = os.path.join("downloads", f"{shortcode}.mp3")
    recipe_path = os.path.join("recipes", f"recipe_{shortcode}.md")

    try:
        caption = get_audio(
            downloader, post_url, firebase_client, shortcode, audio_path, local
        )
        transcript = get_transcript(firebase_client, shortcode, audio_path, verbose)
    except Exception as e:
        logging.error(f"Error processing audio or transcript: {e}")
        return

    if not caption:
        caption = get_caption(downloader, shortcode)

    logging.info("Generating recipe...")
    try:
        recipe_data = generator.generate_recipe(transcript, caption)
        recipe = Recipe(
            recipe_id=shortcode,
            title=recipe_data.get("title"),
            ingredients=recipe_data.get("ingredients"),
            instructions=recipe_data.get("instructions"),
            notes=recipe_data.get("notes"),
            categories=recipe_data.get("categories"),
            firebase_client=firebase_client,
        )
        cookbook.add_recipe(recipe)
    except Exception as e:
        logging.error(f"Error during recipe generation or saving: {e}")
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
        "--local",
        action="store_true",
        default=False,
        help="Save files locally instead of Firestore",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    firebase_client = FirebaseClient(local=args.local)
    downloader = InstagramDownloader(local=args.local)
    generator = RecipeGenerator(
        output_dir="recipes", local=args.local, firebase_client=firebase_client
    )

    # Prompt user for their information or generate IDs
    user_id = input("Enter your user ID (or press Enter to generate one): ")
    if not user_id:
        user_id = str(uuid.uuid4())
        logging.info(f"Generated user ID: {user_id}")

    user_name = input("Enter your name: ")
    user_email = input("Enter your email: ")

    user = User(
        user_id=user_id,
        name=user_name,
        email=user_email,
        firebase_client=firebase_client,
    )
    user.save()

    # Create or select a cookbook
    cookbook_name = input("Enter the name of your cookbook: ")
    cookbook_description = input("Enter a description for your cookbook: ")
    cookbook_id = str(uuid.uuid4())
    logging.info(f"Generated cookbook ID: {cookbook_id}")

    cookbook = Cookbook(
        cookbook_id=cookbook_id,
        name=cookbook_name,
        description=cookbook_description,
        firebase_client=firebase_client,
    )
    user.create_cookbook(cookbook)

    for post_url in args.post_urls:
        process_post(
            downloader,
            post_url,
            user,
            cookbook,
            generator,
            firebase_client,
            verbose=args.debug,
            local=args.local,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An unhandled exception occurred: {e}")
