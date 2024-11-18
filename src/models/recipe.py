from typing import Dict, List, Optional, Union

from firebase.client import FirebaseClient


class Recipe:
    def __init__(
        self,
        recipe_id: str,
        title: str,
        ingredients: List[str],
        instructions: List[str],
        categories: List[str],
        notes: Optional[str] = None,
        firebase_client: Optional[FirebaseClient] = None,
    ) -> None:
        self.recipe_id = recipe_id
        self.title = title
        self.ingredients = ingredients
        self.instructions = instructions
        self.notes = notes
        self.firebase_client = firebase_client or FirebaseClient()
        self.categories = categories

    def save(self) -> None:
        recipe_data = {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "notes": self.notes,
            "categories": self.categories,
        }
        self.firebase_client.save_recipe(self.recipe_id, recipe_data)

    def get_data(self) -> Dict[str, Union[str, List[str]]]:
        return {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "notes": self.notes,
            "categories": self.categories,
        }

    # ...additional methods...
