import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
import logging


class FirebaseClient:
    def __init__(self, firebase_app=None):
        if firebase_app is None:
            if not firebase_admin._apps:
                service_account_path = os.path.join(
                    os.path.dirname(__file__), "../../../.private/firebasekey.json"
                )
                cred = credentials.Certificate(service_account_path)
                firebase_app = firebase_admin.initialize_app(
                    cred,
                    {
                        "storageBucket": "ai-recipe-bot-d0b13.firebasestorage.app",
                        "projectId": "ai-recipe-bot-d0b13",
                    },
                )
        self.db = firestore.client()
        self.bucket = storage.bucket()
        logging.info(
            "Firebase initialized successfully with service account credentials."
        )

    def upload_file(self, local_path, remote_path):
        """
        Upload a file to Firebase Storage.

        Args:
            local_path (str): Path to the local file.
            remote_path (str): Path in Firebase Storage.
        """
        try:
            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            logging.info(f"File uploaded to Firebase Storage at {remote_path}")
        except Exception as e:
            logging.error(f"Error uploading file to Firebase Storage: {e}")

    def upload_string(self, content, remote_path):
        """
        Upload a string content to Firebase Storage.

        Args:
            content (str): Content to upload.
            remote_path (str): Path in Firebase Storage.
        """
        try:
            blob = self.bucket.blob(remote_path)
            blob.upload_from_string(content)
            logging.info(f"Content uploaded to Firebase Storage at {remote_path}")
        except Exception as e:
            logging.error(f"Error uploading content to Firebase Storage: {e}")

    def download_string(self, remote_path):
        """
        Download a string content from Firebase Storage.

        Args:
            remote_path (str): Path in Firebase Storage.

        Returns:
            str: Downloaded content.
        """
        try:
            blob = self.bucket.blob(remote_path)
            content = blob.download_as_text()
            logging.info(f"Content downloaded from Firebase Storage at {remote_path}")
            return content
        except Exception as e:
            logging.error(f"Error downloading content from Firebase Storage: {e}")
            return ""

    def file_exists(self, path):
        """
        Check if a file exists in Firebase Storage.

        Args:
            path (str): Path to the file in Firebase Storage.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            blob = self.bucket.blob(path)
            return blob.exists()
        except Exception as e:
            logging.error(f"Error checking file existence in Firebase: {e}")
            return False

    def document_exists(self, collection, document_id):
        """
        Check if a document exists in Firestore.

        Args:
            collection (str): Firestore collection name.
            document_id (str): Document ID.

        Returns:
            bool: True if the document exists, False otherwise.
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            return doc_ref.get().exists
        except Exception as e:
            logging.error(f"Error checking document existence in Firestore: {e}")
            return False

    def get_document(self, collection, document_id):
        """
        Retrieve a document from Firestore.

        Args:
            collection (str): Firestore collection name.
            document_id (str): Document ID.

        Returns:
            dict: Document data.
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return {}
        except Exception as e:
            logging.error(f"Error retrieving document from Firestore: {e}")
            return {}

    def set_document(self, collection, document_id, data):
        """
        Set a document in Firestore.

        Args:
            collection (str): Firestore collection name.
            document_id (str): Document ID.
            data (dict): Data to set in the document.
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.set(data)
            logging.info(f"Document {document_id} set in collection {collection}")
        except Exception as e:
            logging.error(f"Error setting document in Firestore: {e}")
