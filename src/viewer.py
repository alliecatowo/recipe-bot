import argparse
import logging
import os
import signal
import subprocess
import sys
from typing import Any, List, Tuple, Union

import firebase_admin
from firebase_admin import credentials, storage
from prompt_toolkit import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.widgets import Label, TextArea

from firebase.client import FirebaseClient
from models.cookbook import Cookbook
from models.recipe import Recipe
from models.user import User
from scraper.recipe_generator import RecipeGenerator

logging.basicConfig(level=logging.INFO)


class CLI:
    def __init__(self, firebase_client: FirebaseClient, user_id: str) -> None:
        self.firebase_client = firebase_client
        self.user = User(
            user_id=user_id, name="", email="", firebase_client=firebase_client
        )
        self.recipe_generator = RecipeGenerator(
            local=firebase_client.local, firebase_client=firebase_client
        )
        self.recipes = self._list_recipes()
        self.recipes.append(("exit", "Exit"))
        self.selected_index = 0
        self.text_area = TextArea(text=self._get_recipe_list(), read_only=True)
        self.layout = Layout(HSplit([Label(text="Select a recipe:"), self.text_area]))
        self.app: Application = Application(
            layout=self.layout, key_bindings=self._create_bindings(), full_screen=False
        )

    def _list_recipes(self) -> List[Tuple[str, str]]:
        if self.firebase_client.local:
            recipes_dir = "recipes"
            return [
                (os.path.join(recipes_dir, f), f)
                for f in os.listdir(recipes_dir)
                if f.endswith(".md")
            ]
        else:
            # List recipes from user's cookbooks
            recipes = []
            user_doc = (
                self.firebase_client.db.collection("users")
                .document(self.user.user_id)
                .get()
            )
            user_data = user_doc.to_dict()
            cookbook_ids = user_data.get("cookbooks", [])
            for cookbook_id in cookbook_ids:
                cookbook_doc = (
                    self.firebase_client.db.collection("cookbooks")
                    .document(cookbook_id)
                    .get()
                )
                cookbook_data = cookbook_doc.to_dict()
                recipe_ids = cookbook_data.get("recipes", [])
                for recipe_id in recipe_ids:
                    recipe_doc = (
                        self.firebase_client.db.collection("recipes")
                        .document(recipe_id)
                        .get()
                    )
                    recipe = recipe_doc.to_dict()
                    recipes.append((recipe_id, recipe["title"]))
            return recipes

    def _display_recipe(self, recipe_path: str) -> None:
        recipe_content = self.firebase_client.download_string(recipe_path)
        print(recipe_content)

    def _clear_screen(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _handle_sigint(self, signum: int, frame: Any) -> None:
        print("\nExiting...")
        get_app().exit()

    def _get_recipe_list(self) -> str:
        return "\n".join(
            [
                f"{'>' if i == self.selected_index else ' '} {recipe[1]}"
                for i, recipe in enumerate(self.recipes)
            ]
        )

    def _display_recipe_in_editor(self, recipe_id: str) -> None:
        recipe_doc = (
            self.firebase_client.db.collection("recipes").document(recipe_id).get()
        )
        if not recipe_doc.exists:
            logging.error(f"Recipe with ID {recipe_id} does not exist in Firebase.")
            return
        recipe_data = recipe_doc.to_dict()
        recipe_path = f"recipes/{recipe_id}.md"

        if not os.path.exists(recipe_path):
            # Download recipe content from Firebase Storage
            try:
                recipe_content = self.firebase_client.download_string(
                    f"recipes/recipe_{recipe_id}.md"
                )
            except FileNotFoundError:
                logging.error(
                    f"Remote path recipes/recipe_{recipe_id}.md does not exist in Firebase Storage."
                )
                # Format the recipe content using RecipeGenerator
                recipe_content = self.recipe_generator.format_recipe_as_markdown(
                    recipe_data
                )
                self.recipe_generator.save_recipe(recipe_data, recipe_id)
            with open(recipe_path, "w") as f:
                f.write(recipe_content)
        editor = os.getenv("EDITOR", "vi")
        subprocess.call([editor, recipe_path])

    def _on_up(self, event: Any) -> None:
        if self.selected_index > 0:
            self.selected_index -= 1
        self.text_area.text = self._get_recipe_list()

    def _on_down(self, event: Any) -> None:
        if self.selected_index < len(self.recipes) - 1:
            self.selected_index += 1
        self.text_area.text = self._get_recipe_list()

    def _on_enter(self, event: Any) -> None:
        if self.recipes[self.selected_index] == "Exit":
            self.app.exit()
        else:
            self._display_recipe_in_editor(self.recipes[self.selected_index][0])
            self.text_area.text = self._get_recipe_list()
            self.app.invalidate()
            get_app().invalidate()

    def _create_bindings(self) -> KeyBindings:
        bindings = KeyBindings()
        bindings.add("up")(self._on_up)
        bindings.add("down")(self._on_down)
        bindings.add("enter")(self._on_enter)
        bindings.add("c-c")(self._exit_app)
        return bindings

    def _exit_app(self, event: Any) -> None:
        self.app.exit()

    def run(self) -> None:
        self._clear_screen()
        signal.signal(signal.SIGINT, self._handle_sigint)
        self.app.run()


def main() -> None:
    """
    Main function to list and display recipes.
    """
    parser = argparse.ArgumentParser(description="List and display recipes.")
    parser.add_argument(
        "--local",
        action="store_true",
        default=False,
        help="Use local storage instead of Firebase",
    )
    args = parser.parse_args()

    firebase_client = FirebaseClient(local=args.local)

    # Prompt for user ID
    user_id = input("Enter your user ID: ")

    cli = CLI(firebase_client, user_id)
    try:
        cli.run()
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
