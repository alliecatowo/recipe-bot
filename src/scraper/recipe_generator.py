import json
import logging
import os

import openai

from config.config import OPENAI_API_KEY
from firebase.client import FirebaseClient

openai.api_key = OPENAI_API_KEY


class RecipeGenerator:
    """
    A class to generate recipes from transcriptions using OpenAI's GPT model.

    Attributes:
        output_dir (str): Directory to save the generated recipes.
        local (bool): Whether to save files locally or to Firebase.
        firebase_client (FirebaseClient): Firebase client instance.
    """

    def __init__(self, output_dir="recipes", local=False, firebase_client=None):
        """
        Initialize the RecipeGenerator.

        Args:
            output_dir (str): Directory to save the generated recipes.
            local (bool): Whether to save files locally or to Firebase.
            firebase_client (FirebaseClient, optional): Firebase client instance. Defaults to None.
        """
        self.output_dir = output_dir
        self.local = local
        self.firebase_client = firebase_client or FirebaseClient()
        if not local:
            logging.info("Firebase initialized successfully.")

    def classify_transcript(self, transcript, caption):
        """
        Classify the likelihood that the transcript contains a recipe.

        Args:
            transcript (str): Transcribed text.
            caption (str): Instagram post caption.

        Returns:
            int: Likelihood percentage that the transcript contains a recipe.
        """
        prompt = (
            f"Determine if the following transcript and instagram caption is related to cooking and likely to contain a recipe. "
            f"Respond with a percentage likelihood:\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Caption:\n{caption}\n\n"
            f"Response format: 'Likelihood: X%'"
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            likelihood_str = response.choices[0].message.content.strip()
            likelihood = int(likelihood_str.split(":")[1].strip().replace("%", ""))
            return likelihood
        except Exception as e:
            logging.error(f"Error during classification: {e}")
            return 0

    def generate_recipe(self, transcript, caption):
        """
        Generate a recipe from the transcript and caption.

        Args:
            transcript (str): Transcribed text.
            caption (str): Instagram post caption.

        Returns:
            dict: Generated recipe data.
        """
        likelihood = self.classify_transcript(transcript, caption)
        if (likelihood < 85):
            logging.info("Transcript is unlikely to contain a recipe.")
            raise ValueError("Transcript does not contain a recipe.")

        prompt = (
            "[no prose]\n"
            "[output only JSON]\n"
            f"Extract the recipe details from the following transcript and caption. Do not include any promotional material"
            f"Provide the recipe title, ingredients (as a list), instructions (as a list), categories (as a list) "
            f"and any notes, formatted in JSON.\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Caption:\n{caption}\n\n"
            f"Response format:\n"
            f"{{\n"
            f'  "title": "Recipe Title",\n'
            f'  "ingredients": ["ingredient 1", "ingredient 2"],\n'
            f'  "instructions": ["step 1", "step 2"],\n'
            f'  "notes": "Additional notes"\n'
            f'  "categories": ["category 1", "category 2"]\n'
            f"}}\n"
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.5,
            )
            recipe_json = response.choices[0].message.content.strip()
            recipe_data = json.loads(recipe_json)
            return recipe_data
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse recipe JSON: {e}")
            raise ValueError("Invalid recipe format received from OpenAI.")
        except Exception as e:
            logging.error(f"Error during recipe generation: {e}")
            raise e

    def format_recipe_as_markdown(self, recipe_data):
        """
        Format the recipe data as Markdown.

        Args:
            recipe_data (dict): Generated recipe data.

        Returns:
            str: Recipe formatted as Markdown.
        """
        markdown_content = f"# {recipe_data['title']}\n\n"
        markdown_content += "## Ingredients\n"
        for ingredient in recipe_data["ingredients"]:
            markdown_content += f"- {ingredient}\n"
        markdown_content += "\n## Instructions\n"
        for idx, instruction in enumerate(recipe_data["instructions"], 1):
            markdown_content += f"{idx}. {instruction}\n"
        if recipe_data.get("notes"):
            markdown_content += f"\n## Notes\n{recipe_data['notes']}\n"
        if recipe_data.get("categories"):
            markdown_content += "\n## Tags\n"
            for category in recipe_data["categories"]:
                markdown_content += f"- {category}\n"
        return markdown_content

    def save_recipe(self, recipe_data, shortcode):
        """
        Save the generated recipe.

        Args:
            recipe_data (dict): Generated recipe data.
            shortcode (str): Shortcode of the Instagram post.
        """
        # Format the recipe data as Markdown
        markdown_content = self.format_recipe_as_markdown(recipe_data)

        if self.local:
            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, f"recipe_{shortcode}.md")
            try:
                with open(output_path, "w") as file:
                    file.write(markdown_content)
                if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                    logging.debug(f"Generated Recipe is:\n{markdown_content}\n")
                logging.info(f"Recipe saved to {output_path}")
            except Exception as e:
                logging.error(f"Error saving recipe: {e}")
        else:
            try:
                self.firebase_client.upload_string(
                    markdown_content, f"recipes/recipe_{shortcode}.md"
                )
                logging.info(
                    f"Recipe uploaded to Firebase Storage at recipes/recipe_{shortcode}.md"
                )
            except Exception as e:
                logging.error(f"Error uploading recipe to Firebase Storage: {e}")
