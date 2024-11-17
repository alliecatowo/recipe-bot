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


def list_recipes(firebase_client):
    """
    List all recipes in storage.

    Args:
        firebase_client (FirebaseClient): Firebase client instance.

    Returns:
        list: List of recipe paths.
    """
    if firebase_client.local:
        recipes_dir = "recipes"
        return [
            os.path.join(recipes_dir, f)
            for f in os.listdir(recipes_dir)
            if f.endswith(".md")
        ]
    else:
        blobs = firebase_client.bucket.list_blobs(prefix="recipes/")
        return [blob.name for blob in blobs if blob.name.endswith(".md")]


def display_recipe(firebase_client, recipe_path):
    """
    Display the selected recipe in Markdown format.

    Args:
        firebase_client (FirebaseClient): Firebase client instance.
        recipe_path (str): Path to the recipe file.
    """
    recipe_content = firebase_client.download_string(recipe_path)
    print(recipe_content)


def clear_screen():
    """
    Clear the terminal screen.
    """
    os.system("cls" if os.name == "nt" else "clear")


def handle_sigint(signum, frame):
    """
    Handle SIGINT (Ctrl+C) signal to exit gracefully.
    """
    print("\nExiting...")
    get_app().exit()


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

    recipes = list_recipes(firebase_client)
    if not recipes:
        print("No recipes found.")
        return

    recipes.append("Exit")
    selected_index = 0

    clear_screen()

    signal.signal(signal.SIGINT, handle_sigint)

    def get_recipe_list():
        return "\n".join(
            [
                f"{'>' if i == selected_index else ' '} {os.path.basename(recipe)}"
                for i, recipe in enumerate(recipes)
            ]
        )

    def display_recipe_in_editor(recipe_path):
        """
        Open the selected recipe in the system's default text editor.

        Args:
            recipe_path (str): Path to the recipe file.
        """
        editor = os.getenv("EDITOR", "vi")
        subprocess.call([editor, recipe_path])

    def on_up(event):
        nonlocal selected_index
        if selected_index > 0:
            selected_index -= 1
        text_area.text = get_recipe_list()

    def on_down(event):
        nonlocal selected_index
        if selected_index < len(recipes) - 1:
            selected_index += 1
        text_area.text = get_recipe_list()

    def on_enter(event):
        if recipes[selected_index] == "Exit":
            app.exit()
        else:
            display_recipe_in_editor(recipes[selected_index])
            text_area.text = get_recipe_list()
            app.invalidate()
            get_app().invalidate()  # Explicitly refresh the terminal screen

    bindings = KeyBindings()
    bindings.add("up")(on_up)
    bindings.add("down")(on_down)
    bindings.add("enter")(on_enter)

    def exit_app(event):
        app.exit()

    bindings.add("c-c")(exit_app)  # Bind Ctrl+C to exit the application

    text_area = TextArea(text=get_recipe_list(), read_only=True)
    layout = Layout(HSplit([Label(text="Select a recipe:"), text_area]))

    app = Application(layout=layout, key_bindings=bindings, full_screen=False)
    app.run()


if __name__ == "__main__":
    main()
