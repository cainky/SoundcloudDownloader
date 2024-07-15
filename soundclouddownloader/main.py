import os, sys, re, zipfile, logging, time, random
from utils import validate_url, clean_filename
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
            "outtmpl": "%(title)s",
            "quiet": True,
            "no_warnings": True,
        }

    def download_track(self, track_url, output_dir):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(track_url, download=False)
            filename = ydl.prepare_filename(info)
            clean_name = clean_filename(filename)
            filepath_without_ext = Path(output_dir) / clean_name

            ydl_opts = dict(self.ydl_opts)
            ydl_opts["outtmpl"] = str(filepath_without_ext)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([track_url])

            time.sleep(0.5)  # Small delay to ensure file system update
            if filepath_without_ext.with_suffix(".mp3").exists():
                filepath = filepath_without_ext.with_suffix(".mp3")
            elif filepath_without_ext.exists():
                filepath = filepath_without_ext
            else:
                filepath = None

            if filepath:
                logger.info(f"Successfully downloaded: {filepath}")
                return filepath
            else:
                logger.warning(f"File not found after download: {filepath}")
                # List directory contents for debugging
                dir_contents = list(Path(output_dir).iterdir())
                logger.debug(f"Directory contents: {[str(f) for f in dir_contents]}")

                # Try to find a file with a similar name
                similar_files = [
                    f for f in dir_contents if f.stem.startswith(clean_name)
                ]
                if similar_files:
                    logger.info(f"Found similar file: {similar_files[0]}")
                    return similar_files[0]

                return None

    def download_playlist(
        self, playlist_url, output_dir, max_workers=5, min_delay=3, max_delay=10
    ):
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Downloading to directory: {output_dir}")

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
                filepath = future.result()
                if filepath:
                    downloaded_files.append(filepath)

                # Add random delay after each download
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)

        if downloaded_files:
            zip_filename = output_dir / "playlist.zip"
            self._create_zip(downloaded_files, zip_filename)
            return zip_filename
        else:
            logger.error("No files were successfully downloaded.")
            return None

    def _create_zip(self, files, zip_filename):
        logger.debug(f"Creating zip file: {zip_filename}")
        logger.debug(f"Files to be zipped: {files}")

        logger.info("Zipping files now please wait...")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for file in files:
                if file.exists():
                    logger.debug(f"Adding file to zip: {file}")
                    zipf.write(file, file.name)
                else:
                    logger.warning(f"File not found when creating zip: {file}")


def main():
    logger.remove()
    logger.add(sys.stderr, level="INFO")
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

    downloader = SoundCloudDownloader()
    logger.info("Downloading now please wait...")
    zip_file = downloader.download_playlist(playlist_url, output_dir, max_workers=3)
    if zip_file:
        logger.success(f"Playlist downloaded and zipped: {zip_file}")
    else:
        logger.error("Failed to download playlist.")
        # Add any cleanup code here if needed
    sys.stdout.flush()  # Ensure all output is displayed


if __name__ == "__main__":
    main()
