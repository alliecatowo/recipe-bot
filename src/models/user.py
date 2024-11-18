import logging
import os
from typing import Dict, List, Optional

from firebase.client import FirebaseClient

from .cookbook import Cookbook


class User:
    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        firebase_client: Optional[FirebaseClient] = None,
    ) -> None:
        self.user_id = user_id
        self.name = name
        self.email = email
        self.firebase_client = firebase_client or FirebaseClient()

    def save(self) -> None:
        user_data = {
            "name": self.name,
            "email": self.email,
            "cookbooks": [],  # Initialize cookbooks as an empty array
        }
        self.firebase_client.create_user(self.user_id, user_data)

    def create_cookbook(self, cookbook: Cookbook) -> None:
        cookbook.save(self.user_id)

    def get_user_recipes(self) -> List[Dict]:
        """
        Retrieve all recipes for the user from their cookbooks.

        Returns:
            list: List of recipes.
        """
        recipes = []
        if self.firebase_client.local:
            local_path = f"users/{self.user_id}/cookbooks"
            if os.path.exists(local_path):
                try:
                    for cookbook_file in os.listdir(local_path):
                        cookbook_path = os.path.join(local_path, cookbook_file)
                        with open(cookbook_path, "r") as file:
                            cookbook_data = eval(file.read())
                            recipes.extend(cookbook_data.get("recipes", []))
                    logging.info(
                        f"Recipes for user {self.user_id} downloaded from local storage."
                    )
                except Exception as e:
                    logging.error(f"Error downloading recipes from local storage: {e}")
                    raise e
            else:
                logging.error(f"Local path {local_path} does not exist.")
        else:
            try:
                user_ref = self.firebase_client.db.collection("users").document(
                    self.user_id
                )
                user_doc = user_ref.get()
                if not user_doc.exists:
                    logging.error(f"User {self.user_id} does not exist.")
                    return []
                user_data = user_doc.to_dict()
                for cookbook_id in user_data.get("cookbooks", []):
                    cookbook_ref = self.firebase_client.db.collection(
                        "cookbooks"
                    ).document(cookbook_id)
                    cookbook_doc = cookbook_ref.get()
                    if cookbook_doc.exists:
                        cookbook_data = cookbook_doc.to_dict()
                        recipes.extend(cookbook_data.get("recipes", []))
                    else:
                        logging.error(f"Cookbook with ID {cookbook_id} does not exist.")
            except Exception as e:
                logging.error(f"Error retrieving recipes for user {self.user_id}: {e}")
        return recipes
