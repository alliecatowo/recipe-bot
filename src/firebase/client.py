import logging
import os
from typing import Dict, Optional

import firebase_admin
from firebase_admin import credentials, firestore, storage


class FirebaseClient:
    def __init__(
        self, local: bool = False, firebase_app: Optional[firebase_admin.App] = None
    ):
        self.local: bool = local
        if not local and firebase_app is None:
            if not firebase_admin._apps:
                service_account_path = os.path.join(
                    os.path.dirname(__file__), "../../.private/firebasekey.json"
                )
                cred = credentials.Certificate(service_account_path)
                firebase_app = firebase_admin.initialize_app(
                    cred,
                    {
                        "storageBucket": "ai-recipe-bot-d0b13.firebasestorage.app",
                        "projectId": "ai-recipe-bot-d0b13",
                    },
                )
        if not local:
            self.db: firestore.Client = firestore.client()
            self.bucket: storage.Bucket = storage.bucket()
            logging.info(
                "Firebase initialized successfully with service account credentials."
            )

    def upload_file(self, local_path: str, remote_path: str) -> None:
        """
        Upload a file to Firebase Storage or save it locally.

        Args:
            local_path (str): Path to the local file.
            remote_path (str): Path in Firebase Storage or local storage.
        """
        if self.local:
            os.makedirs(os.path.dirname(remote_path), exist_ok=True)
            try:
                with open(remote_path, "wb") as file:
                    file.write(open(local_path, "rb").read())
                logging.info(f"File saved locally at {remote_path}")
            except Exception as e:
                logging.error(f"Error saving file locally: {e}")
        else:
            try:
                blob = self.bucket.blob(remote_path)
                blob.upload_from_filename(local_path)
                logging.info(f"File uploaded to Firebase Storage at {remote_path}")
            except Exception as e:
                logging.error(f"Error uploading file to Firebase Storage: {e}")

    def upload_string(self, content: str, remote_path: str) -> None:
        """
        Upload a string content to Firebase Storage or save it locally.

        Args:
            content (str): Content to upload.
            remote_path (str): Path in Firebase Storage or local storage.
        """
        if self.local:
            os.makedirs(os.path.dirname(remote_path), exist_ok=True)
            try:
                with open(remote_path, "w") as file:
                    file.write(content)
                logging.info(f"Content saved locally at {remote_path}")
            except Exception as e:
                logging.error(f"Error saving content locally: {e}")
        else:
            try:
                blob = self.bucket.blob(remote_path)
                blob.upload_from_string(content)
                logging.info(f"Content uploaded to Firebase Storage at {remote_path}")
            except Exception as e:
                logging.error(f"Error uploading content to Firebase Storage: {e}")

    def download_string(self, remote_path: str) -> str:
        """
        Download a string content from Firebase Storage or local storage.

        Args:
            remote_path (str): Path in Firebase Storage or local storage.

        Returns:
            str: Downloaded content.

        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: If there is an error during download.
        """
        if self.local:
            if os.path.exists(remote_path):
                try:
                    with open(remote_path, "r") as file:
                        content = file.read()
                    logging.info(
                        f"Content downloaded from local storage at {remote_path}"
                    )
                    return content
                except Exception as e:
                    logging.error(f"Error downloading content from local storage: {e}")
                    raise e
            else:
                logging.error(f"Local path {remote_path} does not exist.")
                raise FileNotFoundError(f"Local path {remote_path} does not exist.")
        else:
            try:
                blob = self.bucket.blob(remote_path)
                if not blob.exists():
                    logging.error(
                        f"Remote path {remote_path} does not exist in Firebase Storage."
                    )
                    raise FileNotFoundError(
                        f"Remote path {remote_path} does not exist in Firebase Storage."
                    )
                content = blob.download_as_text()
                logging.info(
                    f"Content downloaded from Firebase Storage at {remote_path}"
                )
                return content
            except Exception as e:
                logging.error(f"Error downloading content from Firebase Storage: {e}")
                raise e

    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download a file from Firebase Storage or local storage.

        Args:
            remote_path (str): Path in Firebase Storage or local storage.
            local_path (str): Path to save the downloaded file.

        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: If there is an error during download.
        """
        if self.local:
            if os.path.exists(remote_path):
                try:
                    with open(local_path, "wb") as file:
                        file.write(open(remote_path, "rb").read())
                    logging.info(f"File downloaded from local storage at {remote_path}")
                except Exception as e:
                    logging.error(f"Error downloading file from local storage: {e}")
                    raise e
            else:
                logging.error(f"Local path {remote_path} does not exist.")
                raise FileNotFoundError(f"Local path {remote_path} does not exist.")
        else:
            try:
                blob = self.bucket.blob(remote_path)
                if not blob.exists():
                    logging.error(
                        f"Remote path {remote_path} does not exist in Firebase Storage."
                    )
                    raise FileNotFoundError(
                        f"Remote path {remote_path} does not exist in Firebase Storage."
                    )
                blob.download_to_filename(local_path)
                logging.info(f"File downloaded from Firebase Storage at {remote_path}")
            except Exception as e:
                logging.error(f"Error downloading file from Firebase Storage: {e}")
                raise e

    def get_document(
        self, collection: str, document_id: str, local_path: Optional[str] = None
    ) -> Dict:
        """
        Retrieve a document from Firestore or local storage.

        Args:
            collection (str): Firestore collection name.
            document_id (str): Document ID.
            local_path (str, optional): Path in local storage. Defaults to None.

        Returns:
            dict: Document data.

        Raises:
            FileNotFoundError: If the document does not exist.
            Exception: If there is an error during retrieval.
        """
        if self.local and local_path and os.path.exists(local_path):
            try:
                with open(local_path, "r") as file:
                    content = file.read()
                logging.info(f"Document downloaded from local storage at {local_path}")
                return eval(
                    content
                )  # Assuming the local document is stored as a dictionary string
            except Exception as e:
                logging.error(f"Error downloading document from local storage: {e}")
                raise e
        elif not self.local:
            try:
                doc_ref = self.db.collection(collection).document(document_id)
                doc = doc_ref.get()
                if not doc.exists:
                    logging.error(
                        f"Document {document_id} does not exist in collection {collection}."
                    )
                    raise FileNotFoundError(
                        f"Document {document_id} does not exist in collection {collection}."
                    )
                return doc.to_dict()
            except Exception as e:
                logging.error(f"Error retrieving document from Firestore: {e}")
                raise e
        else:
            logging.error(f"Local path {local_path} does not exist.")
            raise FileNotFoundError(f"Local path {local_path} does not exist.")

    def set_document(self, collection: str, document_id: str, data: Dict) -> None:
        """
        Set a document in Firestore or save it locally.

        Args:
            collection (str): Firestore collection name.
            document_id (str): Document ID.
            data (dict): Data to set in the document.
        """
        if self.local:
            local_path = f"{collection}/{document_id}.json"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            try:
                with open(local_path, "w") as file:
                    file.write(str(data))
                logging.info(f"Document saved locally at {local_path}")
            except Exception as e:
                logging.error(f"Error saving document locally: {e}")
        else:
            try:
                doc_ref = self.db.collection(collection).document(document_id)
                doc_ref.set(data)
                logging.info(f"Document {document_id} set in collection {collection}")
            except Exception as e:
                logging.error(f"Error setting document in Firestore: {e}")

    def create_user(self, user_id: str, user_data: Dict) -> None:
        """Create a new user document."""
        if self.local:
            local_path = f"users/{user_id}.json"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w") as file:
                file.write(str(user_data))
        else:
            try:
                user_ref = self.db.collection("users").document(user_id)
                user_ref.set(user_data)
                logging.info(f"User {user_id} created.")
            except Exception as e:
                logging.error(f"Error creating user: {e}")

    def create_cookbook(
        self, user_id: str, cookbook_id: str, cookbook_data: Dict
    ) -> None:
        """Create a new cookbook and associate it with a user."""
        if self.local:
            local_path = f"users/{user_id}/cookbooks/{cookbook_id}.json"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w") as file:
                file.write(str(cookbook_data))
        else:
            try:
                # Save cookbook in 'cookbooks' collection
                cookbook_ref = self.db.collection("cookbooks").document(cookbook_id)
                cookbook_ref.set(cookbook_data)
                # Update user document with reference to the cookbook ID
                user_ref = self.db.collection("users").document(user_id)
                user_ref.update({"cookbooks": firestore.ArrayUnion([cookbook_id])})
                logging.info(
                    f"Cookbook {cookbook_id} created and associated with user {user_id}."
                )
            except Exception as e:
                logging.error(f"Error creating cookbook: {e}")

    def save_recipe(self, recipe_id: str, recipe_data: Dict) -> None:
        """Save a recipe in the 'recipes' collection."""
        if self.local:
            local_path = f"recipes/{recipe_id}.json"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w") as file:
                file.write(str(recipe_data))
        else:
            try:
                recipe_ref = self.db.collection("recipes").document(recipe_id)
                recipe_ref.set(recipe_data)
                logging.info(f"Recipe {recipe_id} saved in 'recipes' collection.")
            except Exception as e:
                logging.error(f"Error saving recipe: {e}")

    def add_recipe_to_cookbook(
        self,
        cookbook_id: str,
        recipe_id: str,
        user_id: Optional[str] = None,
        recipe_data: Optional[Dict] = None,
    ) -> None:
        """Add a recipe to a cookbook or associate a recipe with a cookbook."""
        if self.local:
            if user_id and recipe_data:
                local_path = (
                    f"users/{user_id}/cookbooks/{cookbook_id}/recipes/{recipe_id}.json"
                )
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "w") as file:
                    file.write(str(recipe_data))
            else:
                local_path = f"cookbooks/{cookbook_id}.json"
                if os.path.exists(local_path):
                    try:
                        with open(local_path, "r") as file:
                            cookbook_data = eval(file.read())
                        cookbook_data["recipes"].append(recipe_id)
                        with open(local_path, "w") as file:
                            file.write(str(cookbook_data))
                        logging.info(
                            f"Recipe {recipe_id} associated with cookbook {cookbook_id} locally."
                        )
                    except Exception as e:
                        logging.error(f"Error associating recipe locally: {e}")
                else:
                    logging.error(f"Cookbook {cookbook_id} does not exist locally.")
        else:
            try:
                if user_id and recipe_data:
                    recipe_ref = (
                        self.db.collection("users")
                        .document(user_id)
                        .collection("cookbooks")
                        .document(cookbook_id)
                        .collection("recipes")
                        .document(recipe_id)
                    )
                    recipe_ref.set(recipe_data)
                    logging.info(
                        f"Recipe {recipe_id} added to cookbook {cookbook_id} for user {user_id}."
                    )
                else:
                    cookbook_ref = self.db.collection("cookbooks").document(cookbook_id)
                    cookbook_ref.update({"recipes": firestore.ArrayUnion([recipe_id])})
                    logging.info(
                        f"Recipe {recipe_id} associated with cookbook {cookbook_id}."
                    )
            except Exception as e:
                logging.error(f"Error adding or associating recipe: {e}")
