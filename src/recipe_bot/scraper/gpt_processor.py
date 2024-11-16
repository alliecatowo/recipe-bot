import openai
from config.config import OPENAI_API_KEY


class GPTProcessor:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY

    def generate_recipe(self, transcript, caption):
        prompt = (
            f"Given the following transcript and caption, extract an actionable recipe:\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Caption:\n{caption}\n\n"
            f"Output the recipe in Markdown format."
        )
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4", messages=[{"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error during GPT processing: {e}")
            return ""
