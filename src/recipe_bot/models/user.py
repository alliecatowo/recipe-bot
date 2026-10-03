from recipe_bot.firebase.client import FirebaseClient

from .cookbook import Cookbook


class User:
    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        firebase_client: FirebaseClient | None = None,
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

    def get_user_recipes(self) -> list[str]:
        """
        Retrieve the IDs of every recipe in the user's cookbooks.

        Returns:
            list: Recipe IDs.
        """
        return self.firebase_client.list_user_recipe_ids(self.user_id)

    def has_recipe_for(self, shortcode: str) -> bool:
        """Whether any of the user's recipes came from this Instagram post."""
        for recipe_id in self.get_user_recipes():
            try:
                recipe = self.firebase_client.get_document("recipes", recipe_id)
            except FileNotFoundError:
                continue
            if recipe.get("shortcode") == shortcode:
                return True
        return False
