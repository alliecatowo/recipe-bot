import json
from types import SimpleNamespace

import openai
import pytest

from recipe_bot.firebase.client import FirebaseClient
from recipe_bot.scraper import recipe_generator as rg
from recipe_bot.scraper.downloader import InstagramDownloader


@pytest.fixture
def generator(tmp_path):
    client = FirebaseClient(local=True, local_root=str(tmp_path))
    return rg.RecipeGenerator(
        output_dir=str(tmp_path / "recipes"), local=True, firebase_client=client
    )


def fake_completion(text):
    message = SimpleNamespace(content=text)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def patch_chat(monkeypatch, *texts):
    replies = iter(texts)
    monkeypatch.setattr(
        rg.openai.chat.completions, "create", lambda **_: fake_completion(next(replies))
    )


def test_shortcode_comes_from_the_post_url():
    downloader = InstagramDownloader.__new__(InstagramDownloader)
    assert downloader._get_shortcode("https://www.instagram.com/p/Cabc123/") == "Cabc123"


def test_markdown_lists_ingredients_steps_notes_and_tags(generator):
    markdown = generator.format_recipe_as_markdown(
        {
            "title": "Dal",
            "ingredients": ["lentils", "water"],
            "instructions": ["rinse", "boil"],
            "notes": "Salt at the end.",
            "categories": ["dinner"],
        }
    )
    assert markdown.startswith("# Dal\n")
    assert "- lentils\n- water" in markdown
    assert "1. rinse\n2. boil" in markdown
    assert "## Notes\nSalt at the end." in markdown
    assert "## Tags\n- dinner" in markdown


def test_classification_parses_the_likelihood(generator, monkeypatch):
    patch_chat(monkeypatch, "Likelihood: 92%")
    assert generator.classify_transcript("boil the lentils", "dal") == 92


def test_classification_failure_means_not_a_recipe(generator, monkeypatch):
    patch_chat(monkeypatch, "no idea")
    assert generator.classify_transcript("x", "y") == 0

    def boom(**_):
        raise openai.APIConnectionError(request=None)

    monkeypatch.setattr(rg.openai.chat.completions, "create", boom)
    assert generator.classify_transcript("x", "y") == 0


def test_generate_recipe_builds_a_recipe_from_json(generator, monkeypatch):
    recipe_json = json.dumps(
        {
            "title": "Dal",
            "ingredients": ["lentils"],
            "instructions": ["boil"],
            "categories": ["dinner"],
        }
    )
    patch_chat(monkeypatch, "Likelihood: 95%", recipe_json)
    recipe = generator.generate_recipe("t", "c", generator.firebase_client)
    assert recipe.title == "Dal"
    assert recipe.notes is None


def test_generate_recipe_rejects_low_confidence_and_bad_json(generator, monkeypatch):
    patch_chat(monkeypatch, "Likelihood: 10%")
    with pytest.raises(ValueError, match="does not contain a recipe"):
        generator.generate_recipe("t", "c", generator.firebase_client)

    patch_chat(monkeypatch, "Likelihood: 99%", "{not json")
    with pytest.raises(ValueError, match="Invalid recipe format"):
        generator.generate_recipe("t", "c", generator.firebase_client)

    patch_chat(monkeypatch, "Likelihood: 99%", json.dumps({"title": "Only a title"}))
    with pytest.raises(ValueError, match="missing"):
        generator.generate_recipe("t", "c", generator.firebase_client)


def test_local_recipe_markdown_is_written_under_the_output_dir(generator, tmp_path):
    generator.save_recipe(
        {"title": "Dal", "ingredients": ["lentils"], "instructions": ["boil"]}, "SC1"
    )
    assert (tmp_path / "recipes" / "recipe_SC1.md").read_text().startswith("# Dal")


def test_transcriber_explains_the_missing_extra(monkeypatch):
    import sys

    from recipe_bot.scraper.transcriber import Transcriber

    monkeypatch.setitem(sys.modules, "whisper", None)
    with pytest.raises(RuntimeError, match="--extra transcribe"):
        Transcriber("audio.mp3")
