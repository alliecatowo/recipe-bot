import sys
from scraper.downloader import InstagramDownloader
from scraper.transcriber import Transcriber
from scraper.gpt_processor import GPTProcessor
from scraper.recipe_generator import RecipeGenerator


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <instagram_post_url>")
        return

    post_url = sys.argv[1]
    downloader = InstagramDownloader(post_url)

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
    generator = RecipeGenerator(recipe)
    generator.save_recipe()

    print("Done!")


if __name__ == "__main__":
    main()
