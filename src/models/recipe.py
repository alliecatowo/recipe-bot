from firebase.client import FirebaseClient


class Recipe:
    def __init__(
        self,
        recipe_id,
        title,
        ingredients,
        instructions,
        notes=None,
        firebase_client=None,
    ):
        self.recipe_id = recipe_id
        self.title = title
        self.ingredients = ingredients
        self.instructions = instructions
        self.notes = notes
        self.firebase_client = firebase_client or FirebaseClient()

    def save(self, user_id, cookbook_id):
        recipe_data = {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "notes": self.notes,
        }
        self.firebase_client.add_recipe_to_cookbook(
            user_id, cookbook_id, self.recipe_id, recipe_data
        )

    # ...additional methods...
