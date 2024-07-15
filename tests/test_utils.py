import unittest, tempfile, shutil, os
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from soundclouddownloader.utils import validate_url, clean_filename, create_zip


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

        self.file1 = self.temp_dir / "file1.mp3"
        self.file2 = self.temp_dir / "file2.mp3"
        self.file1.touch()
        self.file2.touch()

        self.files = [self.file1, self.file2]
        self.output_path = self.temp_dir / "test.zip"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_url(self):
        self.assertTrue(validate_url("https://soundcloud.com/playlist"))
        self.assertFalse(validate_url("not a url"))

    def test_clean_filename(self):
        self.assertEqual(clean_filename("Test: File.mp3"), "Test_File.mp3")
        self.assertEqual(clean_filename("Tést Fíle.mp3"), "Test_File.mp3")
        self.assertEqual(clean_filename("a" * 300 + ".mp3"), "a" * 251 + ".mp3")

    def test_validate_url(self):
        self.assertTrue(validate_url("https://soundcloud.com/playlist"))
        self.assertFalse(validate_url("not a url"))

    def test_clean_filename(self):
        self.assertEqual(clean_filename("Test: File.mp3"), "Test_File.mp3")
        self.assertEqual(clean_filename("Tést Fíle.mp3"), "Test_File.mp3")
        self.assertEqual(clean_filename("a" * 300 + ".mp3"), "a" * 251 + ".mp3")

    @patch("zipfile.ZipFile")
    def test_create_zip(self, mock_zipfile):
        create_zip(self.files, self.output_path, self.temp_dir)

        mock_zipfile.assert_called_once_with(self.output_path, "w")
        mock_zip_instance = mock_zipfile.return_value.__enter__.return_value
        self.assertEqual(mock_zip_instance.write.call_count, 2)

        # Check if write was called with correct arguments for both files
        write_calls = mock_zip_instance.write.call_args_list
        expected_calls = [
            (os.path.normpath(str(self.file1)), self.file1.name),
            (os.path.normpath(str(self.file2)), self.file2.name),
        ]

        for expected_call in expected_calls:
            self.assertTrue(
                any(
                    os.path.normpath(call.args[0]) == expected_call[0]
                    and (
                        call.args[1] == expected_call[1]
                        or call.args[1] == Path(expected_call[1])
                    )
                    for call in write_calls
                ),
                f"Expected call not found: {expected_call}",
            )


if __name__ == "__main__":
    unittest.main()
