from recipe_bot.firebase.client import FirebaseClient


class Recipe:
    def __init__(
        self,
        recipe_id: str,
        title: str,
        ingredients: list[str],
        instructions: list[str],
        categories: list[str],
        notes: str | None = None,
        shortcode: str | None = None,
        firebase_client: FirebaseClient | None = None,
    ) -> None:
        self.recipe_id = recipe_id
        self.title = title
        self.ingredients = ingredients
        self.instructions = instructions
        self.notes = notes
        self.shortcode = shortcode  # Instagram post this recipe came from
        self.firebase_client = firebase_client or FirebaseClient()
        self.categories = categories

    def save(self) -> None:
        recipe_data = {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "notes": self.notes,
            "categories": self.categories,
            "shortcode": self.shortcode,
        }
        self.firebase_client.save_recipe(self.recipe_id, recipe_data)

    def get_data(self) -> dict[str, str | list[str]]:
        return {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "notes": self.notes,
            "categories": self.categories,
        }
