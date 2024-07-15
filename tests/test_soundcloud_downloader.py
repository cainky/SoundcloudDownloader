import tempfile, shutil, os
from pathlib import Path
from soundclouddownloader import SoundCloudDownloader
from soundclouddownloader import Track, Playlist

import unittest
from unittest.mock import patch, MagicMock


class TestSoundCloudDownloader(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(os.getcwd()) / "tests" / "temp_test_dir"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(dir=str(self.test_dir)))
        self.downloader = SoundCloudDownloader()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("yt_dlp.YoutubeDL")
    def test_download_track(self, mock_ydl):
        mock_ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance

        mock_ydl_instance.extract_info.return_value = {
            "title": "Test Track",
            "ext": "mp3",
        }

        expected_filename = "Test_Track.mp3"
        mock_ydl_instance.prepare_filename.return_value = expected_filename

        mock_ydl_instance.download.return_value = 0  # Simulate successful download

        track = Track(
            id="track1",
            title="Test Track",
            artist="Test Artist",
            url="https://soundcloud.com/user/track",
        )

        # Create a mock file to simulate successful download
        mock_file = self.temp_dir / expected_filename
        mock_file.touch()

        with patch("time.sleep"):  # Mock sleep to speed up test
            result = self.downloader.download_track(track, self.temp_dir)

        self.assertIsNotNone(result)
        expected_path = self.temp_dir / expected_filename
        self.assertEqual(result, expected_path)
        mock_ydl_instance.download.assert_called()

    @patch("yt_dlp.YoutubeDL")
    def test_get_playlist_info(self, mock_yt_dlp):
        # Mock the yt_dlp behavior
        mock_ydl = MagicMock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "id": "playlist123",
            "title": "Test Playlist",
            "entries": [
                {
                    "id": "track1",
                    "title": "Track 1",
                    "uploader": "Artist 1",
                    "webpage_url": "https://soundcloud.com/track1",
                },
                {
                    "id": "track2",
                    "title": "Track 2",
                    "uploader": "Artist 2",
                    "webpage_url": "https://soundcloud.com/track2",
                },
            ],
        }

        result = self.downloader.get_playlist_info(
            "https://soundcloud.com/test_playlist"
        )

        self.assertIsInstance(result, Playlist)
        self.assertEqual(result.id, "playlist123")
        self.assertEqual(result.title, "Test Playlist")
        self.assertEqual(len(result.tracks), 2)
        self.assertEqual(result.tracks[0].title, "Track 1")
        self.assertEqual(result.tracks[1].artist, "Artist 2")

    @patch("soundclouddownloader.SoundCloudDownloader.get_playlist_info")
    @patch("soundclouddownloader.SoundCloudDownloader.download_track")
    def test_download_playlist(self, mock_download_track, mock_get_playlist_info):
        mock_get_playlist_info.return_value = Playlist(
            id="playlist123",
            title="Test Playlist",
            tracks=[
                Track(
                    id="track1",
                    title="Track 1",
                    artist="Artist 1",
                    url="https://soundcloud.com/track1",
                ),
                Track(
                    id="track2",
                    title="Track 2",
                    artist="Artist 2",
                    url="https://soundcloud.com/track2",
                ),
            ],
        )

        mock_download_track.side_effect = [
            self.temp_dir / "Track 1.mp3",
            self.temp_dir / "Track 2.mp3",
        ]

        result = self.downloader.download_playlist(
            "https://soundcloud.com/test_playlist", self.temp_dir
        )

        self.assertIsNotNone(result)
        self.assertEqual(result, self.temp_dir / "Test Playlist")
        self.assertEqual(mock_download_track.call_count, 2)
