from firebase.client import FirebaseClient


class Recipe:
    def __init__(
        self,
        recipe_id,
        title,
        ingredients,
        instructions,
        categories,
        notes=None,
        firebase_client=None,
    ):
        self.recipe_id = recipe_id
        self.title = title
        self.ingredients = ingredients
        self.instructions = instructions
        self.notes = notes
        self.firebase_client = firebase_client or FirebaseClient()
        self.categories = categories

    def save(self):
        recipe_data = {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "notes": self.notes,
            "categories": self.categories,
        }
        self.firebase_client.save_recipe(self.recipe_id, recipe_data)

    def get_data(self):
        return {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "notes": self.notes,
            "categories": self.categories,
        }

    # ...additional methods...
