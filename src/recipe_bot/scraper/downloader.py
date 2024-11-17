import instaloader
import os
import requests


class InstagramDownloader:
    def __init__(self, post_url):
        self.post_url = post_url
        self.loader = instaloader.Instaloader()

    def download_content(self, output_dir="downloads"):
        os.makedirs(output_dir, exist_ok=True)
        try:
            # Get the post details using instaloader
            post = instaloader.Post.from_shortcode(
                self.loader.context, self._get_shortcode()
            )
            caption = post.caption
            video_url = post.video_url

            # Download video directly from the URL
            video_path = os.path.join(output_dir, f"{self._get_shortcode()}.mp4")
            self._download_video(video_url, video_path)

            return video_path, caption
        except Exception as e:
            print(f"Error downloading content: {e}")
            return None, None

    def _get_shortcode(self):
        # Extract the shortcode from the post URL
        return self.post_url.split("/")[-2]

    def _download_video(self, video_url, output_path):
        # Download video file using requests
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()  # Raise HTTPError for bad responses
            with open(output_path, "wb") as video_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        video_file.write(chunk)
            print(f"Video successfully downloaded to {output_path}")
        except requests.RequestException as e:
            print(f"Error downloading video: {e}")
