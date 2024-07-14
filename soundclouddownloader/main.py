import os
import re
import zipfile
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import yt_dlp  # We use yt-dlp, a more actively maintained fork of youtube-dl

class SoundCloudDownloader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

    def download_track(self, track_url, output_dir):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(track_url, download=False)
                filename = ydl.prepare_filename(info)
                filename = os.path.splitext(filename)[0] + '.mp3'
                filepath = os.path.join(output_dir, filename)
                
                ydl_opts = dict(self.ydl_opts)
                ydl_opts['outtmpl'] = filepath
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([track_url])
                
                return filepath
        except Exception as e:
            self.logger.error(f"Failed to download track {track_url}: {e}")
            return None

    def download_playlist(self, playlist_url, output_dir, max_workers=5):
        os.makedirs(output_dir, exist_ok=True)

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            tracks = playlist_info['entries']

        downloaded_files = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_track = {executor.submit(self.download_track, track['webpage_url'], output_dir): track for track in tracks}
            for future in as_completed(future_to_track):
                track = future_to_track[future]
                try:
                    filepath = future.result()
                    if filepath:
                        downloaded_files.append(filepath)
                        self.logger.info(f"Downloaded: {track['title']}")
                except Exception as e:
                    self.logger.error(f"Error downloading {track['title']}: {e}")

        zip_filename = os.path.join(output_dir, "playlist.zip")
        self._create_zip(downloaded_files, zip_filename)
        return zip_filename

    def _create_zip(self, files, zip_filename):
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file in files:
                zipf.write(file, os.path.basename(file))
                os.remove(file)  # Remove the original file after adding to zip

def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and 'soundcloud.com' in result.netloc
    except ValueError:
        return False

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    while True:
        playlist_url = input("Enter SoundCloud playlist URL: ")
        if validate_url(playlist_url):
            break
        print("Invalid URL. Please enter a valid SoundCloud playlist URL.")

    output_dir = input("Enter output directory (default: current directory): ").strip() or '.'

    try:
        downloader = SoundCloudDownloader()
        zip_file = downloader.download_playlist(playlist_url, output_dir)
        print(f"Playlist downloaded and zipped: {zip_file}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()