import os


class RecipeGenerator:
    def __init__(self, recipe_text, output_dir="recipes"):
        self.recipe_text = recipe_text
        self.output_dir = output_dir

    def save_recipe(self, shortcode):
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, f"recipe_{shortcode}.md")
        try:
            with open(output_path, "w") as file:
                file.write(self.recipe_text)
            print(f"Recipe saved to {output_path}")
        except Exception as e:
            print(f"Error saving recipe: {e}")
