# Instagram Recipe Scraper

**Instagram Recipe Scraper** is a Python-based tool that extracts actionable recipes from Instagram posts. By analyzing captions and video audio transcripts, it generates well-structured recipes in Markdown format. I intend to scale this up to a full-fledged web application in the future, but for now, it's a command-line tool MVP.

This project uses:
- [Instaloader](https://instaloader.github.io) to download Instagram posts.
- [FFmpeg](https://ffmpeg.org) for audio extraction.
- [Pydub](https://pydub.com) for audio processing.
- [Whisper API](https://openai.com/whisper) for audio transcription.
- [OpenAI GPT](https://openai.com/api) to generate the recipe from text inputs.
- [Firebase Storage](https://firebase.google.com/docs/storage) for storing audio files and recipes.
- [Firestore](https://firebase.google.com/docs/firestore) for storing metadata and associations.

---

## Features

- 🥗 **Automatic Recipe Extraction**: Turn Instagram video captions and audio into structured recipes.
- 📥 **Download Instagram Content**: Fetch videos and captions from Instagram posts.
- 📝 **Markdown Output**: Save recipes as easy-to-read `.md` files.
- 🧠 **AI-Powered**: Leverages OpenAI's Whisper for transcription and GPT for recipe generation.
- 👀 **Recipe Viewer**: View and edit saved recipes using a simple CLI interface.
- ☁️ **Cloud Storage**: Store audio files and recipes in Firebase Storage.
- 📊 **Metadata Management**: Use Firestore to manage metadata and associations.

---

## Requirements

- Python 3.8+
- [PDM](https://pdm.fming.dev/latest/) for dependency management
- [FFmpeg](https://ffmpeg.org) for audio extraction.
- An OpenAI API key for Whisper and GPT integrations.
- A Firebase project with Firestore and Firebase Storage enabled.

---

## Installation

### Clone the Repository
```bash
git clone https://github.com/yourusername/instagram-recipe-scraper.git
cd instagram-recipe-scraper
```

### Install PDM
```bash
pip install pdm
```

### Install Dependencies
```bash
pdm install
```

### Set the OpenAI API Key
Export your OpenAI API key to the environment:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### Set the Firebase Service Account Key
Export the path to your Firebase service account key to the environment:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-file.json"
```

### Platform-Specific Instructions

#### Linux
Ensure you have the necessary CUDA libraries for GPU acceleration:
```bash
sudo apt-get install nvidia-cuda-toolkit
```

#### macOS
No additional steps are required.

#### Windows
Ensure you have the necessary CUDA libraries for GPU acceleration:
1. Download and install the [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads).
2. Set the `CUDA_PATH` environment variable to the installation path.

---

## Usage

To run the tool, use the following command:
```bash
pdm run python 

main.py

 <instagram_post_url> <recipe_name>
```

### Example
```bash
pdm run python 

main.py

 https://www.instagram.com/p/example/ "Example Recipe"
```

The program will:
1. Download the Instagram video and caption.
2. Extract the audio and transcribe it using Whisper API.
3. Generate a recipe using OpenAI GPT.
4. Save the recipe to a Markdown file in the `recipes/` folder.
5. Upload the audio file and recipe to Firebase Storage.
6. Store metadata in Firestore.

---

View and Edit Recipes
To view and edit recipes using the CLI interface, run:
```bash
python src/viewer.py [--local]
```
--local: Use local storage instead of Firebase

## Adding Dependencies

To add a new dependency, run:
```bash
pdm add <package-name>
```

To remove a dependency, run:
```bash
pdm remove <package-name>
```

---

## Contributing

### Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for our commit messages. Here are some common types:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation

### Example Commit Messages

- `feat: add support for Firebase Storage`
- `fix: correct audio extraction logic`
- `docs: update README with new installation instructions`
- `style: format code with black`
- `refactor: restructure project directories`
- `perf: optimize transcription process`
- `test: add unit tests for downloader`
- `chore: update dependencies`

### Steps to Contribute

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "feat: add your feature description"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Open a pull request.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Support

If you encounter any issues, feel free to [open an issue](https://github.com/alliecatowo/recipe-bot/issues) or reach out to `allisonemilycoleman@gmail.com`.

Happy scraping! 🎉
