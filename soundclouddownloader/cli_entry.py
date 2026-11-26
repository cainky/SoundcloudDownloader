import argparse
import os
from pathlib import Path
from loguru import logger
from soundclouddownloader.main import SoundCloudDownloader


def run(
    playlist_url: str,
    output_dir: Path,
    should_zip: bool = False,
    proxy: str = None,
    oauth_token: str = None,
    audio_format: str = "mp3",
):
    """
    Run the download using non-interactive input (for CLI or GitHub Actions).

    Args:
        playlist_url (str): The URL of the SoundCloud playlist
        output_dir (Path): The directory to save downloads
        should_zip (bool): Whether to zip the downloaded files
        proxy (str): Optional proxy URL to use for downloads
        oauth_token (str): Optional SoundCloud OAuth token (Go+ unlocks 256kbps AAC)
        audio_format (str): Output codec, "mp3" (default) or "best" to skip re-encoding
    """
    downloader = SoundCloudDownloader(
        proxy=proxy, oauth_token=oauth_token, audio_format=audio_format
    )
    result = downloader.download_playlist(
        playlist_url, output_dir, max_workers=3, should_zip=should_zip
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI for SoundCloud Downloader")
    parser.add_argument("--url", required=True, help="SoundCloud playlist URL")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--proxy", help="Proxy URL (e.g., http://proxy.example.com:8080)")
    parser.add_argument("--zip", action="store_true", help="Zip the downloaded files")
    parser.add_argument(
        "--oauth-token",
        default=os.environ.get("SOUNDCLOUD_OAUTH_TOKEN"),
        help="SoundCloud OAuth token (or set SOUNDCLOUD_OAUTH_TOKEN). Go+ accounts get 256kbps AAC",
    )
    parser.add_argument(
        "--audio-format",
        default="mp3",
        help='Output codec: "mp3" (default), "best" to keep the original stream, or any FFmpegExtractAudio codec',
    )
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    run(
        args.url,
        output_path,
        args.zip,
        args.proxy,
        oauth_token=args.oauth_token or None,
        audio_format=args.audio_format,
    )
