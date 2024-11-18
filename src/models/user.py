from firebase.client import FirebaseClient


class User:
    def __init__(self, user_id, name, email, firebase_client=None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.firebase_client = firebase_client or FirebaseClient()

    def save(self):
        user_data = {
            "name": self.name,
            "email": self.email,
        }
        self.firebase_client.create_user(self.user_id, user_data)

    def create_cookbook(self, cookbook):
        cookbook.save(self.user_id)
