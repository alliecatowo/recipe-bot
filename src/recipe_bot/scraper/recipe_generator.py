import os
import logging
import openai
from config.config import OPENAI_API_KEY

class RecipeGenerator:
    def __init__(self, output_dir="recipes"):
        self.output_dir = output_dir
        openai.api_key = OPENAI_API_KEY

    def generate_recipe(self, transcript, caption, save=True, shortcode=None):
        prompt = (
            f"Given the following transcript and caption, extract an actionable recipe:\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Caption:\n{caption}\n\n"
            f"Output the recipe in Markdown format."
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
            )
            recipe = response.choices[0].message.content
            if save and shortcode:
                self.save_recipe(recipe, shortcode)
            return recipe
        except Exception as e:
            logging.error(f"Error during GPT processing: {e}")
            return ""

    def save_recipe(self, recipe_text, shortcode):
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, f"recipe_{shortcode}.md")
        try:
            with open(output_path, "w") as file:
                file.write(recipe_text)
            logging.info(f"Recipe saved to {output_path}")
        except Exception as e:
            logging.error(f"Error saving recipe: {e}")
