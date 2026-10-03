import logging

from recipe_bot.firebase.client import FirebaseClient

from .recipe import Recipe


class Cookbook:
    def __init__(
        self,
        cookbook_id: str,
        name: str,
        description: str,
        firebase_client: FirebaseClient | None = None,
    ) -> None:
        self.cookbook_id = cookbook_id
        self.name = name
        self.description = description
        self.firebase_client = firebase_client or FirebaseClient()
        self.user_id: str | None = None

    def save(self, user_id: str) -> None:
        cookbook_data = {
            "name": self.name,
            "description": self.description,
            "recipes": [],  # Initialize recipes as an empty array
        }
        self.firebase_client.create_cookbook(user_id, self.cookbook_id, cookbook_data)
        self.user_id = user_id

    def add_recipe(self, recipe: Recipe) -> None:
        """Save the recipe and add it to this cookbook.

        Raises:
            ValueError: If the cookbook has not been saved for a user yet.
            StorageError: If either write fails.
        """
        if self.user_id is None:
            raise ValueError("Save the cookbook for a user before adding recipes.")
        recipe.save()
        self.firebase_client.add_recipe_to_cookbook(
            self.user_id, self.cookbook_id, recipe.recipe_id
        )
        logging.info(f"Recipe {recipe.recipe_id} associated with cookbook {self.cookbook_id}.")
