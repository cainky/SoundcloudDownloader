import os
import re
import zipfile
import logging
import time
from utils import validate_url
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
from loguru import logger


class SoundCloudDownloader:
    def __init__(self):
        self.ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
        }

    def download_track(self, track_url, output_dir):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(track_url, download=False)
                filename = ydl.prepare_filename(info)
                filename = Path(filename).stem  # Remove all extensions
                filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
                filename = f"{filename}.mp3"  # Add .mp3 extension
                filepath = output_dir / filename

                ydl_opts = dict(self.ydl_opts)
                ydl_opts["outtmpl"] = str(filepath)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([track_url])

                time.sleep(0.5)  # Small delay to ensure file system update

                if filepath.exists():
                    logger.info(f"Successfully downloaded: {filepath}")
                    return filepath
                else:
                    logger.warning(f"File not found after download: {filepath}")
                    # List directory contents for debugging
                    dir_contents = list(output_dir.iterdir())
                    logger.debug(f"Directory contents: {dir_contents}")

                    # Try to find a file with a similar name
                    similar_files = [
                        f
                        for f in dir_contents
                        if f.stem.startswith(Path(filename).stem)
                    ]
                    if similar_files:
                        logger.info(f"Found similar file: {similar_files[0]}")
                        return similar_files[0]

                    return None
        except Exception as e:
            logger.error(f"Failed to download track {track_url}: {e}")
            return None

    def download_playlist(
        self, playlist_url, output_dir, max_workers=5, min_delay=1, max_delay=5
    ):
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading to directory: {output_dir}")

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            tracks = playlist_info["entries"]

        downloaded_files = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_track = {
                executor.submit(
                    self.download_track, track["webpage_url"], output_dir
                ): track
                for track in tracks
            }
            for future in as_completed(future_to_track):
                track = future_to_track[future]
                try:
                    filepath = future.result()
                    if filepath:
                        downloaded_files.append(filepath)

                    # Add random delay after each download
                    delay = random.uniform(min_delay, max_delay)
                    time.sleep(delay)

                except Exception as e:
                    logger.error(f"Error downloading {track['title']}: {e}")

        if downloaded_files:
            zip_filename = output_dir / "playlist.zip"
            self._create_zip(downloaded_files, zip_filename)
            return zip_filename
        else:
            logger.error("No files were successfully downloaded.")
            return None

    def _create_zip(self, files, zip_filename):
        logger.info(f"Creating zip file: {zip_filename}")
        logger.debug(f"Files to be zipped: {files}")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for file in files:
                if file.exists():
                    logger.debug(f"Adding file to zip: {file}")
                    zipf.write(file, file.name)
                    file.unlink()  # Remove the original file after adding to zip
                else:
                    logger.warning(f"File not found when creating zip: {file}")


def main():
    logger.add("soundcloud_downloader.log", rotation="10 MB", level="INFO")

    while True:
        playlist_url = input("Enter SoundCloud playlist URL: ")
        if validate_url(playlist_url):
            break
        logger.warning("Invalid URL. Please enter a valid SoundCloud playlist URL.")

    cwd = Path.cwd()
    output_dir_input = (
        input("Enter output directory (default: output): ").strip() or "output"
    )
    output_dir = cwd / output_dir_input
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        downloader = SoundCloudDownloader()
        zip_file = downloader.download_playlist(
            playlist_url, output_dir, max_workers=3, min_delay=2, max_delay=5
        )
        if zip_file:
            logger.success(f"Playlist downloaded and zipped: {zip_file}")
        else:
            logger.error("Failed to download playlist.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
