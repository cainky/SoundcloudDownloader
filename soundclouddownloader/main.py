import os, sys, re, logging, time, random, shutil
from soundclouddownloader.utils import validate_url, clean_filename, create_zip
from soundclouddownloader.dataclass import Track, Playlist
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
from loguru import logger
from typing import List, Optional, Dict, Any

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("soundcloud_downloader.log", rotation="10 MB", level="INFO")


class SoundCloudDownloader:
    """
    A class to download tracks and playlists from SoundCloud.

    This class provides methods to download individual tracks and entire playlists
    from SoundCloud, using yt-dlp as the backend.
    """

    def __init__(self):
        """
        Initialize the SoundCloudDownloader with default yt-dlp options.
        """
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

    def download_track(self, track: Track, output_dir: Path) -> Optional[Path]:
        """
        Download a single track from SoundCloud.

        Args:
            track (Track): The Track object to download.
            output_dir (Path): The directory to save the downloaded track.

        Returns:
            Optional[Path]: The path to the downloaded file, or None if download failed.
        """
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(track.url, download=False)
            filename = ydl.prepare_filename(info)
            clean_name = clean_filename(filename)
            filepath_without_ext = Path(output_dir) / clean_name

            ydl_opts = dict(self.ydl_opts)
            ydl_opts["outtmpl"] = str(filepath_without_ext)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([track.url])

            time.sleep(0.5)  # Small delay to ensure file system update
            if filepath_without_ext.with_suffix(".mp3").exists():
                filepath = filepath_without_ext.with_suffix(".mp3")
            elif filepath_without_ext.exists():
                filepath = filepath_without_ext
            else:
                filepath = None

            if not filepath:
                dir_contents = list(Path(output_dir).iterdir())

                # Try to find a file with a similar name
                similar_files = [
                    f for f in dir_contents if f.stem.startswith(clean_name)
                ]
                if similar_files:
                    filepath = similar_files[0]
                if not filepath:
                    logger.info(
                        f"File not found after download: {filepath_without_ext}"
                    )
                    logger.debug(
                        f"Directory contents: {[str(f) for f in dir_contents]}"
                    )
                    return None

            logger.info(f"Successfully downloaded: {filepath}")
            return filepath

    def get_playlist_info(self, playlist_url: str) -> Playlist:
        """
        Extract playlist information from SoundCloud.

        Args:
            playlist_url (str): The URL of the playlist.

        Returns:
            Playlist: A Playlist object containing the playlist information.
        """
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            tracks = [
                Track(
                    id=track["id"],
                    title=track["title"],
                    artist=track["uploader"],
                    url=track["webpage_url"],
                )
                for track in playlist_info["entries"]
            ]
            return Playlist(
                id=playlist_info["id"], title=playlist_info["title"], tracks=tracks
            )

    def download_playlist(
        self,
        playlist_url: str,
        output_dir: Path,
        max_workers: int = 5,
        min_delay: int = 3,
        max_delay: int = 10,
        should_zip: bool = False,
    ) -> Optional[Path]:
        """
        Download an entire playlist from SoundCloud.

        Args:
            playlist_url (str): The URL of the playlist to download.
            output_dir (Path): The directory to save the downloaded tracks.
            max_workers (int, optional): Maximum number of concurrent downloads. Defaults to 5.
            min_delay (int, optional): Minimum delay between downloads in seconds. Defaults to 3.
            max_delay (int, optional): Maximum delay between downloads in seconds. Defaults to 10.
            should_zip (bool, optional): Whether to zip the downloaded files. Defaults to False.

        Returns:
            Optional[Path]: The path to the zipped playlist or playlist directory, or None if download failed.
        """
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Downloading to directory: {output_dir}")

        playlist = self.get_playlist_info(playlist_url)
        playlist_name = clean_filename(playlist.title)
        playlist_dir = output_dir / playlist_name
        playlist_dir.mkdir(exist_ok=True)

        downloaded_files: List[Path] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_track = {
                executor.submit(self.download_track, track, playlist_dir): track
                for track in playlist.tracks
            }
            for future in as_completed(future_to_track):
                track = future_to_track[future]
                filepath = future.result()
                if filepath:
                    downloaded_files.append(filepath)

                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)

        if downloaded_files:
            if should_zip:
                zip_filename = output_dir / f"{playlist_name}.zip"
                create_zip(downloaded_files, zip_filename, playlist_dir)
                for file in downloaded_files:
                    file.unlink()  # Delete original files after zipping
                shutil.rmtree(playlist_dir)
                return zip_filename
            else:
                return playlist_dir
        else:
            logger.error("No files were successfully downloaded.")
            return None


def main() -> None:
    """
    Main function to run the SoundCloud downloader.

    This function sets up logging, prompts the user for input,
    and initiates the download process.
    """

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

    while True:
        should_zip = input("Do you want to zip the downloaded files? (y/n): ").lower()
        if should_zip in ["y", "n"]:
            should_zip = should_zip == "y"
            break
        logger.warning("Invalid input. Please enter 'y' for yes or 'n' for no.")

    downloader = SoundCloudDownloader()
    logger.info("Downloading now please wait...")
    download = downloader.download_playlist(
        playlist_url, output_dir, max_workers=3, should_zip=should_zip
    )
    if download:
        logger.success(f"Playlist downloaded: {download}")
    else:
        logger.error("Failed to download playlist.")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
