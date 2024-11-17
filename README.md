# Instagram Recipe Scraper

**Instagram Recipe Scraper** is a Python-based tool that extracts actionable recipes from Instagram posts. By analyzing captions and video audio transcripts, it generates well-structured recipes in Markdown format. I intend to scale this up to a full-fledged web application in the future, but for now, it's a command-line tool MVP.

This project uses:
- [Instaloader](https://instaloader.github.io) to download Instagram posts.
- [FFmpeg](https://ffmpeg.org) for audio extraction.
- [Pydub](https://pydub.com) for audio processing.
- [Whisper API](https://openai.com/whisper) for audio transcription.
- [OpenAI GPT](https://openai.com/api) to generate the recipe from text inputs.

---

## Features

- 🥗 **Automatic Recipe Extraction**: Turn Instagram video captions and audio into structured recipes.
- 📥 **Download Instagram Content**: Fetch videos and captions from Instagram posts.
- 📝 **Markdown Output**: Save recipes as easy-to-read `.md` files.
- 🧠 **AI-Powered**: Leverages OpenAI's Whisper for transcription and GPT for recipe generation.

---

## Requirements

- Python 3.8+
- [PDM](https://pdm.fming.dev/latest/) for dependency management
- [FFmpeg](https://ffmpeg.org) for audio extraction.
- An OpenAI API key for Whisper and GPT integrations.

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
pdm run python main.py <instagram_post_url>
```

### Example
```bash
pdm run python main.py https://www.instagram.com/p/example/
```

The program will:
1. Download the Instagram video and caption.
2. Extract the audio and transcribe it using Whisper API.
3. Generate a recipe using OpenAI GPT.
4. Save the recipe to a Markdown file in the `recipes/` folder.

---

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

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your feature description"
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

If you encounter any issues, feel free to [open an issue](https://github.com/alliecatowo/instagram-recipe-scraper/issues) or reach out to `allisonemilycoleman@gmail.com`.

Happy scraping! 🎉
