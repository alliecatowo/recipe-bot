import sys
import os
import logging
from scraper.downloader import InstagramDownloader
from scraper.transcriber import Transcriber
from scraper.gpt_processor import GPTProcessor
from scraper.recipe_generator import RecipeGenerator

logging.basicConfig(level=logging.INFO)

def process_post(post_url):
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
    transcript = transcriber.transcribe_audio()

    logging.info("Generating recipe...")
    gpt_processor = GPTProcessor()
    recipe = gpt_processor.generate_recipe(transcript, caption)

    logging.info("Saving recipe...")
    generator = RecipeGenerator(recipe, output_dir="recipes")
    generator.save_recipe(shortcode=shortcode)

    logging.info("Done!")

def main():
    if len(sys.argv) < 2:
        post_urls = [input("Please enter the Instagram post URL(s): ")]
    else:
        post_urls = sys.argv[1:]

    for post_url in post_urls:
        process_post(post_url)

if __name__ == "__main__":
    main()
