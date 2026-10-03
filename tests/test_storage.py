import json

import pytest

from recipe_bot.firebase.client import FirebaseClient, StorageError


@pytest.fixture
def client(tmp_path):
    return FirebaseClient(local=True, local_root=str(tmp_path))


def test_documents_round_trip_as_json(client, tmp_path):
    client.set_document("recipes", "r1", {"title": "Dal", "ingredients": ["lentils"]})

    stored = json.loads((tmp_path / "recipes" / "r1.json").read_text())
    assert stored == {"title": "Dal", "ingredients": ["lentils"]}
    assert client.get_document("recipes", "r1") == stored


def test_legacy_str_dict_files_still_load(client, tmp_path):
    legacy = tmp_path / "recipes" / "old.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(str({"title": "Old", "notes": None}))

    assert client.get_document("recipes", "old") == {"title": "Old", "notes": None}


def test_missing_document_is_file_not_found(client):
    with pytest.raises(FileNotFoundError):
        client.get_document("recipes", "nope")


def test_corrupt_document_is_a_storage_error(client, tmp_path):
    bad = tmp_path / "recipes" / "bad.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("not a document {")

    with pytest.raises(StorageError):
        client.get_document("recipes", "bad")


def test_strings_and_files_round_trip(client, tmp_path):
    client.upload_string("# Dal", "recipes/recipe_abc.md")
    assert client.download_string("recipes/recipe_abc.md") == "# Dal"

    source = tmp_path / "in.mp3"
    source.write_bytes(b"audio")
    client.upload_file(str(source), "audio/abc.mp3")
    target = tmp_path / "out" / "abc.mp3"
    client.download_file("audio/abc.mp3", str(target))
    assert target.read_bytes() == b"audio"


def test_upload_of_a_missing_source_file_is_file_not_found(client, tmp_path):
    with pytest.raises(FileNotFoundError):
        client.upload_file(str(tmp_path / "missing.mp3"), "audio/x.mp3")
