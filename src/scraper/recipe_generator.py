import os
import logging
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
                model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
            )
            likelihood_str = response.choices[0].message.content
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
            str: Generated recipe in Markdown format.
        """
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
            return recipe
        except Exception as e:
            logging.error(f"Error during GPT processing: {e}")
            return ""

    def save_recipe(self, recipe_text, shortcode):
        """
        Save the generated recipe.

        Args:
            recipe_text (str): Generated recipe text.
            shortcode (str): Shortcode of the Instagram post.
        """
        if self.local:
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
        else:
            try:
                self.firebase_client.upload_string(
                    recipe_text, f"recipes/recipe_{shortcode}.md"
                )
                logging.info(
                    f"Recipe uploaded to Firebase Storage at recipes/recipe_{shortcode}.md"
                )
            except Exception as e:
                logging.error(f"Error uploading recipe to Firebase Storage: {e}")
