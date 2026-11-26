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

    @patch("yt_dlp.YoutubeDL")
    def test_get_playlist_info_skips_unextractable_entries(self, mock_yt_dlp):
        # yt-dlp with ignoreerrors=True returns None entries for tracks
        # it couldn't extract (e.g. upstream 404 / DRM-protected tracks).
        # We should skip those and return the rest, not crash.
        mock_ydl = MagicMock()
        mock_yt_dlp.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "id": "playlist123",
            "title": "Mixed Playlist",
            "entries": [
                {
                    "id": "track1",
                    "title": "Track 1",
                    "uploader": "Artist 1",
                    "webpage_url": "https://soundcloud.com/track1",
                },
                None,  # yt-dlp couldn't extract this one
                {
                    "id": "track3",
                    "title": "Track 3",
                    "uploader": "Artist 3",
                    "webpage_url": "https://soundcloud.com/track3",
                },
            ],
        }

        result = self.downloader.get_playlist_info(
            "https://soundcloud.com/test_playlist"
        )

        self.assertIsInstance(result, Playlist)
        self.assertEqual(len(result.tracks), 2)
        self.assertEqual(result.tracks[0].id, "track1")
        self.assertEqual(result.tracks[1].id, "track3")

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

    def test_default_options_unchanged(self):
        d = SoundCloudDownloader()
        pp = d.ydl_opts["postprocessors"][0]
        self.assertEqual(pp["preferredcodec"], "mp3")
        self.assertEqual(pp["preferredquality"], "192")
        self.assertNotIn("username", d.ydl_opts)
        self.assertNotIn("password", d.ydl_opts)

    def test_oauth_token_sets_login(self):
        d = SoundCloudDownloader(oauth_token="abc123")
        self.assertEqual(d.ydl_opts["username"], "oauth")
        self.assertEqual(d.ydl_opts["password"], "abc123")
        # MP3 output bumps to 320 when logged in so HQ streams aren't wasted
        self.assertEqual(d.ydl_opts["postprocessors"][0]["preferredquality"], "320")

    def test_audio_format_best_skips_reencode(self):
        d = SoundCloudDownloader(audio_format="best")
        pp = d.ydl_opts["postprocessors"][0]
        self.assertEqual(pp["preferredcodec"], "best")
        self.assertNotIn("preferredquality", pp)

    @patch("yt_dlp.YoutubeDL")
    def test_download_track_best_format_finds_file(self, mock_ydl):
        mock_ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {"title": "HQ Track"}
        mock_ydl_instance.prepare_filename.return_value = "HQ_Track"

        mock_file = self.temp_dir / "HQ_Track.m4a"
        mock_file.touch()

        d = SoundCloudDownloader(audio_format="best")
        track = Track(id="t", title="HQ Track", artist="A", url="https://soundcloud.com/u/t")
        with patch("time.sleep"):
            result = d.download_track(track, self.temp_dir)
        self.assertEqual(result, mock_file)
        # Without an explicit ext in outtmpl, "best" saves extensionless files
        download_opts = mock_ydl.call_args_list[-1][0][0]
        self.assertTrue(download_opts["outtmpl"].endswith(".%(ext)s"))

    @patch("time.sleep")
    @patch.object(SoundCloudDownloader, "_download_track_once")
    def test_download_track_retries_on_rate_limit(self, mock_once, mock_sleep):
        rate_limited = Exception(
            "ERROR: [soundcloud] x: Unable to download JSON metadata: HTTP Error 403: Forbidden"
        )
        mock_once.side_effect = [rate_limited, rate_limited, self.temp_dir / "ok.mp3"]
        track = Track(id="t", title="T", artist="A", url="https://soundcloud.com/u/t")
        result = self.downloader.download_track(track, self.temp_dir)
        self.assertEqual(result, self.temp_dir / "ok.mp3")
        self.assertEqual(mock_once.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep")
    @patch.object(SoundCloudDownloader, "_download_track_once")
    def test_download_track_gives_up_after_max_retries(self, mock_once, mock_sleep):
        mock_once.side_effect = Exception("HTTP Error 429: Too Many Requests")
        track = Track(id="t", title="T", artist="A", url="https://soundcloud.com/u/t")
        self.assertIsNone(self.downloader.download_track(track, self.temp_dir))
        self.assertEqual(
            mock_once.call_count, len(SoundCloudDownloader.RATE_LIMIT_BACKOFF) + 1
        )

    @patch("time.sleep")
    @patch.object(SoundCloudDownloader, "_download_track_once")
    def test_download_track_no_retry_on_drm(self, mock_once, mock_sleep):
        mock_once.side_effect = Exception("This video is DRM protected")
        track = Track(id="t", title="T", artist="A", url="https://soundcloud.com/u/t")
        self.assertIsNone(self.downloader.download_track(track, self.temp_dir))
        self.assertEqual(mock_once.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("yt_dlp.YoutubeDL")
    def test_get_playlist_info_single_track_url(self, mock_ydl):
        mock_ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            "id": "123",
            "title": "Solo",
            "uploader": "Artist",
            "webpage_url": "https://soundcloud.com/a/solo",
        }
        playlist = self.downloader.get_playlist_info("https://soundcloud.com/a/solo")
        self.assertEqual(playlist.title, "Solo")
        self.assertEqual(len(playlist.tracks), 1)
        self.assertEqual(playlist.tracks[0].url, "https://soundcloud.com/a/solo")

    @patch("yt_dlp.YoutubeDL")
    def test_get_playlist_info_unextractable_url(self, mock_ydl):
        mock_ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = None
        with self.assertRaisesRegex(ValueError, "Could not extract"):
            self.downloader.get_playlist_info("https://soundcloud.com/a/drm")
