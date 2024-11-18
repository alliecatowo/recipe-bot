from typing import Optional

from recipe import Recipe

from firebase.client import FirebaseClient


class Cookbook:
    def __init__(
        self,
        cookbook_id: str,
        name: str,
        description: str,
        firebase_client: Optional[FirebaseClient] = None,
    ) -> None:
        self.cookbook_id = cookbook_id
        self.name = name
        self.description = description
        self.firebase_client = firebase_client or FirebaseClient()

    def save(self, user_id: str) -> None:
        cookbook_data = {
            "name": self.name,
            "description": self.description,
            "recipes": [],  # Initialize recipes as an empty array
        }
        self.firebase_client.create_cookbook(user_id, self.cookbook_id, cookbook_data)

    def add_recipe(self, recipe: Recipe) -> None:
        recipe.save()
        self.firebase_client.add_recipe_to_cookbook(self.cookbook_id, recipe.recipe_id)
