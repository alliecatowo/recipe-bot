import os
import sys
import logging
import argparse
import firebase_admin
from firebase_admin import credentials, storage
import subprocess
import signal

from firebase.client import FirebaseClient
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.widgets import TextArea, Label
from prompt_toolkit.application.current import get_app

logging.basicConfig(level=logging.INFO)


class CLI:
    def __init__(self, firebase_client):
        self.firebase_client = firebase_client
        self.recipes = self.list_recipes()
        self.recipes.append("Exit")
        self.selected_index = 0
        self.text_area = TextArea(text=self.get_recipe_list(), read_only=True)
        self.layout = Layout(HSplit([Label(text="Select a recipe:"), self.text_area]))
        self.app = Application(layout=self.layout, key_bindings=self.create_bindings(), full_screen=False)

    def list_recipes(self):
        if self.firebase_client.local:
            recipes_dir = "recipes"
            return [
                os.path.join(recipes_dir, f)
                for f in os.listdir(recipes_dir)
                if f.endswith(".md")
            ]
        else:
            blobs = self.firebase_client.bucket.list_blobs(prefix="recipes/")
            return [blob.name for blob in blobs if blob.name.endswith(".md")]

    def display_recipe(self, recipe_path):
        recipe_content = self.firebase_client.download_string(recipe_path)
        print(recipe_content)

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def handle_sigint(self, signum, frame):
        print("\nExiting...")
        get_app().exit()

    def get_recipe_list(self):
        return "\n".join(
            [
                f"{'>' if i == self.selected_index else ' '} {os.path.basename(recipe)}"
                for i, recipe in enumerate(self.recipes)
            ]
        )

    def display_recipe_in_editor(self, recipe_path):
        if not os.path.exists(recipe_path):
            recipe_content = self.firebase_client.download_string(recipe_path)
            with open(recipe_path, "w") as f:
                f.write(recipe_content)
        editor = os.getenv("EDITOR", "vi")
        subprocess.call([editor, recipe_path])

    def on_up(self, event):
        if self.selected_index > 0:
            self.selected_index -= 1
        self.text_area.text = self.get_recipe_list()

    def on_down(self, event):
        if self.selected_index < len(self.recipes) - 1:
            self.selected_index += 1
        self.text_area.text = self.get_recipe_list()

    def on_enter(self, event):
        if self.recipes[self.selected_index] == "Exit":
            self.app.exit()
        else:
            self.display_recipe_in_editor(self.recipes[self.selected_index])
            self.text_area.text = self.get_recipe_list()
            self.app.invalidate()
            get_app().invalidate()

    def create_bindings(self):
        bindings = KeyBindings()
        bindings.add("up")(self.on_up)
        bindings.add("down")(self.on_down)
        bindings.add("enter")(self.on_enter)
        bindings.add("c-c")(self.exit_app)
        return bindings

    def exit_app(self, event):
        self.app.exit()

    def run(self):
        self.clear_screen()
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.app.run()

def main():
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
    cli = CLI(firebase_client)
    cli.run()


if __name__ == "__main__":
    main()
