from typing import Optional

from cookbook import Cookbook

from firebase.client import FirebaseClient


class User:
    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        firebase_client: Optional[FirebaseClient] = None,
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
