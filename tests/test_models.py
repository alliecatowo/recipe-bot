import pytest

from recipe_bot.firebase.client import FirebaseClient
from recipe_bot.models import Cookbook, Recipe, User


@pytest.fixture
def client(tmp_path):
    return FirebaseClient(local=True, local_root=str(tmp_path))


def make_recipe(client, recipe_id="r1", shortcode="SC1"):
    return Recipe(
        recipe_id=recipe_id,
        title="Dal",
        ingredients=["lentils", "water"],
        instructions=["boil"],
        categories=["dinner"],
        shortcode=shortcode,
        firebase_client=client,
    )


def test_recipe_save_persists_the_source_shortcode(client):
    make_recipe(client).save()
    assert client.get_document("recipes", "r1")["shortcode"] == "SC1"


def test_cookbook_collects_recipes_for_its_user(client):
    user = User("u1", "Ada", "ada@example.com", firebase_client=client)
    user.save()
    cookbook = Cookbook("c1", "Weeknights", "Quick dinners", firebase_client=client)
    user.create_cookbook(cookbook)

    cookbook.add_recipe(make_recipe(client, "r1", "SC1"))
    cookbook.add_recipe(make_recipe(client, "r2", "SC2"))

    assert user.get_user_recipes() == ["r1", "r2"]
    assert user.has_recipe_for("SC2")
    assert not user.has_recipe_for("SC3")


def test_adding_a_recipe_before_saving_the_cookbook_fails_loudly(client):
    cookbook = Cookbook("c1", "Weeknights", "Quick dinners", firebase_client=client)
    with pytest.raises(ValueError):
        cookbook.add_recipe(make_recipe(client))


def test_user_without_cookbooks_has_no_recipes(client):
    user = User("nobody", "N", "n@example.com", firebase_client=client)
    assert user.get_user_recipes() == []
    assert not user.has_recipe_for("SC1")
