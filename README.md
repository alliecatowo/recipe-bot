# Instagram Recipe Scraper

**Instagram Recipe Scraper** is a Python-based tool that extracts actionable recipes from Instagram posts. By analyzing captions and video audio transcripts, it generates well-structured recipes in Markdown format.  

This project uses:
- [Instaloader](https://instaloader.github.io) to download Instagram posts.
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
- An OpenAI API key for Whisper and GPT integrations.

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/instagram-recipe-scraper.git
   cd instagram-recipe-scraper
   ```

2. **Install PDM**:
   ```bash
   pip install pdm
   ```

3. **Install Dependencies**:
   ```bash
   pdm install
   ```

4. **Set the OpenAI API Key**:
   Export your OpenAI API key to the environment:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

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

If you encounter any issues, feel free to [open an issue](https://github.com/yourusername/instagram-recipe-scraper/issues) or reach out to `your.email@example.com`.

Happy scraping! 🎉