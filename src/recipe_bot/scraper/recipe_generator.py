import os
import logging
import openai
from config.config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


class RecipeGenerator:
    def __init__(self, output_dir="recipes"):
        self.output_dir = output_dir

    def classify_transcript(self, transcript, caption):
        prompt = (
            f"Determine if the following transcript and instagram caption is related to cooking and likely to contain a recipe. "
            f"Respond with a percentage likelihood:\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Caption:\n{caption}\n\n"
            f"Response format: 'Likelihood: X%'"
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
            )
            likelihood_str = response.choices[0].message.content
            likelihood = int(likelihood_str.split(":")[1].strip().replace("%", ""))
            return likelihood
        except Exception as e:
            logging.error(f"Error during classification: {e}")
            return 0

    
    def generate_recipe(self, transcript, caption, save=True, shortcode=None):
        likelihood = self.classify_transcript(transcript, caption)
        if likelihood < 85:
            logging.info(
                "The transcript is not likely to contain a recipe. Please try another video."
            )
            raise ValueError("Transcript does not contain a recipe.")

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
            if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                logging.debug(f"Generated Recipe is:\n{recipe_text}\n")
            logging.info(f"Recipe saved to {output_path}")
        except Exception as e:
            logging.error(f"Error saving recipe: {e}")
