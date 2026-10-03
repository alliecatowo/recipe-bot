# Recipe Bot

Turn an Instagram cooking video into a written recipe. Give it a post URL and it downloads the video, transcribes the audio with Whisper, asks GPT whether the post really contains a recipe, extracts the title, ingredients, steps and tags as structured JSON, and files the result in a cookbook (Firestore and Firebase Storage, or plain files with `--local`).

```console
# abridged example
$ uv run recipe-bot --local https://www.instagram.com/p/Cabc123/
Enter your user ID (or press Enter to generate one):
...
INFO:root:Generating recipe...
INFO:root:Done!

$ cat recipes/recipe_Cabc123.md
# Weeknight Dal

## Ingredients
- 1 cup red lentils
- 3 cups water
...
```

A browser UI is planned; for now this is a command-line tool. [recipe-bot on allisons.dev](https://allisons.dev/projects/recipe-bot/).

## Install

You need [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you) and [FFmpeg](https://ffmpeg.org) on your `PATH` for audio extraction.

```bash
git clone https://github.com/alliecatowo/recipe-bot && cd recipe-bot
uv sync --extra transcribe   # --extra transcribe adds local Whisper and PyTorch (several GB)
```

## Configure

```bash
export OPENAI_API_KEY="sk-..."                       # recipe extraction
export GOOGLE_APPLICATION_CREDENTIALS=".private/firebasekey.json"   # Firebase mode only
```

Firebase mode uses the project and bucket in `RECIPE_BOT_PROJECT_ID` and `RECIPE_BOT_STORAGE_BUCKET` (defaults to the author's project, so set your own). `--local` needs neither Firebase nor credentials: documents are stored as JSON under the working directory (`users/`, `recipes/`, `transcripts/`, ...).

## Use

```bash
uv run recipe-bot [--local] [--debug] <instagram_post_url> [<url> ...]
uv run recipe-bot-view [--local]      # browse and edit saved recipes in $EDITOR
```

Recipes are saved as Markdown in `recipes/`, with the audio and transcript cached so re-running a post is cheap. A post that does not look like a recipe (GPT confidence under 85%) is skipped.

## Develop

```bash
uv sync                 # without the Whisper/PyTorch extra
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy
uv run pytest
```

CI runs exactly that. The code lives in `src/recipe_bot/`: `scraper/` (download, transcribe, generate), `models/` (user, cookbook, recipe), `firebase/` (storage with a local-disk mode), `main.py` and `viewer.py` (the two commands). Dependabot keeps dependencies and workflows current and auto-merges patch and minor updates once CI is green.

## License

[MIT](LICENSE)
