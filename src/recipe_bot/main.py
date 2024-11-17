import sys
import os
from scraper.downloader import InstagramDownloader
from scraper.transcriber import Transcriber
from scraper.gpt_processor import GPTProcessor
from scraper.recipe_generator import RecipeGenerator


def main():
    if len(sys.argv) < 2:
        post_url = input("Please enter the Instagram post URL: ")
    else:
        post_url = sys.argv[1]

    downloader = InstagramDownloader(post_url)
    shortcode = downloader._get_shortcode()
    video_path = os.path.join("downloads", f"{shortcode}.mp4")
    recipe_path = os.path.join("recipes", f"recipe_{shortcode}.md")

    if os.path.exists(video_path) and os.path.exists(recipe_path):
        print(f"Video and recipe for {shortcode} already exist.")
        return

    print("Downloading content...")
    video_path, caption = downloader.download_content()
    if not video_path or not caption:
        print("Failed to download content.")
        return

    print("Transcribing audio...")
    transcriber = Transcriber(video_path)
    transcript = transcriber.transcribe_audio()

    print("Generating recipe...")
    gpt_processor = GPTProcessor()
    recipe = gpt_processor.generate_recipe(transcript, caption)

    print("Saving recipe...")
    generator = RecipeGenerator(recipe, output_dir="recipes")
    generator.save_recipe(shortcode=shortcode)

    print("Done!")


if __name__ == "__main__":
    main()
