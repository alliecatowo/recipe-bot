import os
import sys
import logging
import argparse
import firebase_admin
from firebase_admin import credentials, storage


from firebase.client import FirebaseClient
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.widgets import TextArea, Label

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

    selected_index = 0

    def get_recipe_list():
        return "\n".join(
            [
                f"{'>' if i == selected_index else ' '} {os.path.basename(recipe)}"
                for i, recipe in enumerate(recipes)
            ]
        )

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
        display_recipe(firebase_client, recipes[selected_index])
        app.exit()

    bindings = KeyBindings()
    bindings.add("up")(on_up)
    bindings.add("down")(on_down)
    bindings.add("enter")(on_enter)

    text_area = TextArea(text=get_recipe_list(), read_only=True)
    layout = Layout(HSplit([Label(text="Select a recipe:"), text_area]))

    app = Application(layout=layout, key_bindings=bindings, full_screen=True)
    app.run()


if __name__ == "__main__":
    main()
