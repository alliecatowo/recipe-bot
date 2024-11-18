from firebase.client import FirebaseClient


class Cookbook:
    def __init__(self, cookbook_id, name, description, firebase_client=None):
        self.cookbook_id = cookbook_id
        self.name = name
        self.description = description
        self.firebase_client = firebase_client or FirebaseClient()

    def save(self, user_id):
        cookbook_data = {
            "name": self.name,
            "description": self.description,
        }
        self.firebase_client.create_cookbook(user_id, self.cookbook_id, cookbook_data)

    def add_recipe(self, user_id, recipe):
        recipe.save(user_id, self.cookbook_id)
