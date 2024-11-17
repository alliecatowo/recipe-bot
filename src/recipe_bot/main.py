import os
import logging
import argparse
import warnings  # Import warnings module
from scraper.downloader import InstagramDownloader
from scraper.transcriber import Transcriber
from scraper.recipe_generator import RecipeGenerator

logging.basicConfig(level=logging.INFO)

# Suppress specific FutureWarning from torch.load
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="You are using `torch.load` with `weights_only=False`",
)


def process_post(post_url, verbose=False):
    downloader = InstagramDownloader(post_url)
    shortcode = downloader._get_shortcode()
    audio_path = os.path.join("downloads", f"{shortcode}.wav")
    recipe_path = os.path.join("recipes", f"recipe_{shortcode}.md")

    if os.path.exists(audio_path) and os.path.exists(recipe_path):
        logging.info(f"Audio and recipe for {shortcode} already exist.")
        return

    logging.info("Downloading content...")
    audio_path, caption = downloader.download_content()
    if not audio_path or not caption:
        logging.error("Failed to download content.")
        return

    logging.info("Transcribing audio...")
    transcriber = Transcriber(audio_path)
    transcript = transcriber.transcribe_audio(verbose)

    logging.info("Generating recipe...")
    generator = RecipeGenerator(output_dir="recipes")
    recipe = generator.generate_recipe(
        transcript, caption, save=True, shortcode=shortcode
    )

    if verbose or logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        logging.info(f"Generated recipe:\n{recipe}")

    logging.info("Done!")


def main():
    parser = argparse.ArgumentParser(
        description="Process Instagram post URLs to generate recipes."
    )
    parser.add_argument(
        "post_urls", nargs="+", help="Instagram post URL(s), seperated by spaces"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    for post_url in args.post_urls:
        process_post(post_url, verbose=args.debug)


if __name__ == "__main__":
    main()
