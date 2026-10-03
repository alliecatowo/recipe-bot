import ast
import json
import logging
import os

import firebase_admin  # type: ignore
from firebase_admin import credentials, firestore, storage
from google.api_core.exceptions import GoogleAPIError


class StorageError(RuntimeError):
    """A read or write against local or Firebase storage failed."""


# What a failed local read/write or Firebase call can raise. Anything else is a bug and
# should surface as itself rather than be logged and swallowed.
_STORAGE_FAILURES = (OSError, GoogleAPIError)


def _parse_document(content: str, source: str) -> dict:
    """Parse a local document. Older runs wrote ``str(dict)``, so fall back to that."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(content)
        except (ValueError, SyntaxError) as e:
            raise StorageError(f"{source} is not a valid JSON document") from e


class FirebaseClient:
    """Firestore and Storage access, with a ``local`` mode that mirrors both on disk.

    In local mode every path is resolved under ``local_root`` (the working directory
    by default), documents are stored as JSON at ``<collection>/<id>.json`` and files
    at their remote path.
    """

    def __init__(
        self,
        local: bool = False,
        firebase_app: firebase_admin.App | None = None,
        local_root: str = ".",
    ):
        self.local: bool = local
        self.local_root: str = local_root
        if not local and firebase_app is None and not firebase_admin._apps:
            service_account_path = os.environ.get(
                "GOOGLE_APPLICATION_CREDENTIALS", os.path.join(".private", "firebasekey.json")
            )
            cred = credentials.Certificate(service_account_path)
            firebase_app = firebase_admin.initialize_app(
                cred,
                {
                    "storageBucket": os.environ.get(
                        "RECIPE_BOT_STORAGE_BUCKET", "ai-recipe-bot-d0b13.firebasestorage.app"
                    ),
                    "projectId": os.environ.get("RECIPE_BOT_PROJECT_ID", "ai-recipe-bot-d0b13"),
                },
            )
        if not local:
            self.db: firestore.Client = firestore.client()
            self.bucket: storage.Bucket = storage.bucket()
            logging.info("Firebase initialized successfully with service account credentials.")

    # -- local helpers -------------------------------------------------------------

    def local_path(self, relative_path: str) -> str:
        """Where ``relative_path`` lives on disk in local mode."""
        return os.path.join(self.local_root, relative_path)

    def _write_local_text(self, relative_path: str, content: str) -> None:
        path = self.local_path(relative_path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

    def _write_local_document(self, relative_path: str, data: dict) -> None:
        self._write_local_text(relative_path, json.dumps(data, indent=2))

    def _read_local_document(self, relative_path: str) -> dict:
        path = self.local_path(relative_path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Local path {path} does not exist.")
        with open(path, encoding="utf-8") as file:
            return _parse_document(file.read(), path)

    # -- files and strings ---------------------------------------------------------

    def upload_file(self, local_path: str, remote_path: str) -> None:
        """
        Upload a file to Firebase Storage or copy it into local storage.

        Args:
            local_path (str): Path to the local file.
            remote_path (str): Path in Firebase Storage or local storage.

        Raises:
            StorageError: If the upload fails.
        """
        try:
            if self.local:
                destination = self.local_path(remote_path)
                os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
                with open(local_path, "rb") as source, open(destination, "wb") as target:
                    target.write(source.read())
                logging.info(f"File saved locally at {destination}")
            else:
                self.bucket.blob(remote_path).upload_from_filename(local_path)
                logging.info(f"File uploaded to Firebase Storage at {remote_path}")
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not upload {local_path} to {remote_path}: {e}") from e

    def upload_string(self, content: str, remote_path: str) -> None:
        """
        Upload string content to Firebase Storage or save it locally.

        Args:
            content (str): Content to upload.
            remote_path (str): Path in Firebase Storage or local storage.

        Raises:
            StorageError: If the upload fails.
        """
        try:
            if self.local:
                self._write_local_text(remote_path, content)
                logging.info(f"Content saved locally at {self.local_path(remote_path)}")
            else:
                self.bucket.blob(remote_path).upload_from_string(content)
                logging.info(f"Content uploaded to Firebase Storage at {remote_path}")
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not upload content to {remote_path}: {e}") from e

    def download_string(self, remote_path: str) -> str:
        """
        Download string content from Firebase Storage or local storage.

        Args:
            remote_path (str): Path in Firebase Storage or local storage.

        Returns:
            str: Downloaded content.

        Raises:
            FileNotFoundError: If the file does not exist.
            StorageError: If the download fails.
        """
        try:
            if self.local:
                path = self.local_path(remote_path)
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Local path {path} does not exist.")
                with open(path, encoding="utf-8") as file:
                    content = file.read()
                logging.info(f"Content downloaded from local storage at {path}")
                return content
            blob = self.bucket.blob(remote_path)
            if not blob.exists():
                raise FileNotFoundError(
                    f"Remote path {remote_path} does not exist in Firebase Storage."
                )
            content = blob.download_as_text()
            logging.info(f"Content downloaded from Firebase Storage at {remote_path}")
            return content
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not download {remote_path}: {e}") from e

    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download a file from Firebase Storage or local storage.

        Args:
            remote_path (str): Path in Firebase Storage or local storage.
            local_path (str): Path to save the downloaded file.

        Raises:
            FileNotFoundError: If the file does not exist.
            StorageError: If the download fails.
        """
        try:
            if self.local:
                source = self.local_path(remote_path)
                if not os.path.exists(source):
                    raise FileNotFoundError(f"Local path {source} does not exist.")
                os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
                with open(source, "rb") as src, open(local_path, "wb") as target:
                    target.write(src.read())
                logging.info(f"File downloaded from local storage at {source}")
                return
            blob = self.bucket.blob(remote_path)
            if not blob.exists():
                raise FileNotFoundError(
                    f"Remote path {remote_path} does not exist in Firebase Storage."
                )
            blob.download_to_filename(local_path)
            logging.info(f"File downloaded from Firebase Storage at {remote_path}")
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not download {remote_path}: {e}") from e

    # -- documents -----------------------------------------------------------------

    def get_document(self, collection: str, document_id: str) -> dict:
        """
        Retrieve a document from Firestore or local storage.

        Args:
            collection (str): Firestore collection name.
            document_id (str): Document ID.

        Returns:
            dict: Document data.

        Raises:
            FileNotFoundError: If the document does not exist.
            StorageError: If the read fails.
        """
        try:
            if self.local:
                return self._read_local_document(f"{collection}/{document_id}.json")
            doc = self.db.collection(collection).document(document_id).get()
            if not doc.exists:
                raise FileNotFoundError(
                    f"Document {document_id} does not exist in collection {collection}."
                )
            return doc.to_dict()
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not read {collection}/{document_id}: {e}") from e

    def set_document(self, collection: str, document_id: str, data: dict) -> None:
        """
        Set a document in Firestore or save it locally.

        Args:
            collection (str): Firestore collection name.
            document_id (str): Document ID.
            data (dict): Data to set in the document.

        Raises:
            StorageError: If the write fails.
        """
        try:
            if self.local:
                self._write_local_document(f"{collection}/{document_id}.json", data)
                logging.info(f"Document saved locally at {collection}/{document_id}.json")
            else:
                self.db.collection(collection).document(document_id).set(data)
                logging.info(f"Document {document_id} set in collection {collection}")
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not write {collection}/{document_id}: {e}") from e

    def create_user(self, user_id: str, user_data: dict) -> None:
        """Create a new user document."""
        self.set_document("users", user_id, user_data)

    def create_cookbook(self, user_id: str, cookbook_id: str, cookbook_data: dict) -> None:
        """Create a new cookbook and associate it with a user."""
        try:
            if self.local:
                self._write_local_document(
                    f"users/{user_id}/cookbooks/{cookbook_id}.json", cookbook_data
                )
            else:
                self.db.collection("cookbooks").document(cookbook_id).set(cookbook_data)
                self.db.collection("users").document(user_id).update(
                    {"cookbooks": firestore.ArrayUnion([cookbook_id])}
                )
                logging.info(f"Cookbook {cookbook_id} created and associated with user {user_id}.")
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not create cookbook {cookbook_id}: {e}") from e

    def add_recipe_to_cookbook(self, user_id: str, cookbook_id: str, recipe_id: str) -> None:
        """Append a recipe ID to a cookbook."""
        try:
            if self.local:
                relative = f"users/{user_id}/cookbooks/{cookbook_id}.json"
                cookbook = self._read_local_document(relative)
                cookbook.setdefault("recipes", []).append(recipe_id)
                self._write_local_document(relative, cookbook)
            else:
                self.db.collection("cookbooks").document(cookbook_id).update(
                    {"recipes": firestore.ArrayUnion([recipe_id])}
                )
            logging.info(f"Recipe {recipe_id} associated with cookbook {cookbook_id}.")
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(
                f"Could not add recipe {recipe_id} to cookbook {cookbook_id}: {e}"
            ) from e

    def list_user_recipe_ids(self, user_id: str) -> list[str]:
        """Every recipe ID across the user's cookbooks."""
        recipes: list[str] = []
        try:
            if self.local:
                directory = self.local_path(f"users/{user_id}/cookbooks")
                if not os.path.isdir(directory):
                    logging.error(f"Local path {directory} does not exist.")
                    return recipes
                for name in sorted(os.listdir(directory)):
                    with open(os.path.join(directory, name), encoding="utf-8") as file:
                        recipes.extend(_parse_document(file.read(), name).get("recipes", []))
                return recipes
            user_doc = self.db.collection("users").document(user_id).get()
            if not user_doc.exists:
                logging.error(f"User {user_id} does not exist.")
                return recipes
            for cookbook_id in user_doc.to_dict().get("cookbooks", []):
                cookbook_doc = self.db.collection("cookbooks").document(cookbook_id).get()
                if cookbook_doc.exists:
                    recipes.extend(cookbook_doc.to_dict().get("recipes", []))
                else:
                    logging.error(f"Cookbook with ID {cookbook_id} does not exist.")
            return recipes
        except FileNotFoundError:
            raise
        except _STORAGE_FAILURES as e:
            raise StorageError(f"Could not list recipes for user {user_id}: {e}") from e

    def save_recipe(self, recipe_id: str, recipe_data: dict) -> None:
        """Save a recipe in the 'recipes' collection."""
        self.set_document("recipes", recipe_id, recipe_data)
