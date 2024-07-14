import requests
import re
import os
import zipfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional, Dict
import logging
from urllib.parse import urlparse, parse_qs
from tqdm import tqdm

@dataclass
class Track:
    id: int
    title: str
    artist: str
    url: str

class SoundCloudAPI:
    BASE_URL = "https://api-v2.soundcloud.com"
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def _make_request(self, url: str, params: Dict[str, str] = None) -> Dict:
        if params is None:
            params = {}
        params['client_id'] = self.client_id

        retries = 3
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def get_playlist_info(self, playlist_url: str) -> Dict:
        resolved = self._make_request(f"{self.BASE_URL}/resolve", params={"url": playlist_url})
        return self._make_request(resolved['uri'])

    def get_track_info(self, track_id: int) -> Dict:
        return self._make_request(f"{self.BASE_URL}/tracks/{track_id}")

class SoundCloudDownloader:
    def __init__(self, client_id: str):
        self.api = SoundCloudAPI(client_id)
        self.logger = logging.getLogger(__name__)

    def get_playlist_tracks(self, playlist_url: str) -> List[Track]:
        playlist_info = self.api.get_playlist_info(playlist_url)
        return [
            Track(
                id=track['id'],
                title=track['title'],
                artist=track['user']['username'],
                url=track['permalink_url']
            )
            for track in playlist_info['tracks']
        ]

    def download_track(self, track: Track, output_dir: str) -> Optional[str]:
        try:
            track_info = self.api.get_track_info(track.id)
            stream_url = track_info['media']['transcodings'][0]['url']
            stream_info = self.api._make_request(stream_url)
            audio_url = stream_info['url']

            filename = f"{track.artist} - {track.title}.mp3"
            filename = re.sub(r'[^\w\-_\. ]', '_', filename)
            filepath = os.path.join(output_dir, filename)

            response = requests.get(audio_url, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return filepath
        except Exception as e:
            self.logger.error(f"Failed to download track {track.title}: {e}")
            return None

    def download_playlist(self, playlist_url: str, output_dir: str, max_workers: int = 5) -> str:
    tracks = self.get_playlist_tracks(playlist_url)
    os.makedirs(output_dir, exist_ok=True)

    downloaded_files = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(self.download_track, track, output_dir): track for track in tracks}
        
        for future in as_completed(futures):
            track = futures[future]
            try:
                result = future.result()
                if result:
                    downloaded_files.append(result)
                    self.logger.info(f"Downloaded: {track.title}")
            except Exception as e:
                self.logger.error(f"Error downloading {track.title}: {e}")

    zip_filename = os.path.join(output_dir, "playlist.zip")
    self._create_zip(downloaded_files, zip_filename)
    return zip_filename


    def _create_zip(self, files: List[str], zip_filename: str):
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

    client_id = os.getenv('SOUNDCLOUD_CLIENT_ID')
    if not client_id:
        logger.error("SOUNDCLOUD_CLIENT_ID environment variable is not set")
        return

    while True:
        playlist_url = input("Enter SoundCloud playlist URL: ")
        if validate_url(playlist_url):
            break
        print("Invalid URL. Please enter a valid SoundCloud playlist URL.")

    output_dir = input("Enter output directory (default: current directory): ").strip() or '.'

    try:
        downloader = SoundCloudDownloader(client_id)
        zip_file = downloader.download_playlist(playlist_url, output_dir)
        print(f"Playlist downloaded and zipped: {zip_file}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
