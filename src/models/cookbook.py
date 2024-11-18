import logging
import os
from typing import Optional

from google.cloud import firestore  # type: ignore

from firebase.client import FirebaseClient

from .recipe import Recipe


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
        if self.firebase_client.local:
            local_path = f"cookbooks/{self.cookbook_id}.json"
            if os.path.exists(local_path):
                try:
                    with open(local_path, "r") as file:
                        cookbook_data = eval(file.read())
                    cookbook_data["recipes"].append(recipe.recipe_id)
                    with open(local_path, "w") as file:
                        file.write(str(cookbook_data))
                    logging.info(
                        f"Recipe {recipe.recipe_id} associated with cookbook {self.cookbook_id} locally."
                    )
                except Exception as e:
                    logging.error(f"Error associating recipe locally: {e}")
            else:
                logging.error(f"Cookbook {self.cookbook_id} does not exist locally.")
        else:
            try:
                cookbook_ref = self.firebase_client.db.collection("cookbooks").document(
                    self.cookbook_id
                )
                cookbook_ref.update(
                    {"recipes": firestore.ArrayUnion([recipe.recipe_id])}
                )
                logging.info(
                    f"Recipe {recipe.recipe_id} associated with cookbook {self.cookbook_id}."
                )
            except Exception as e:
                logging.error(f"Error associating recipe: {e}")
