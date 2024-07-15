import unittest, tempfile, os, shutil
from pathlib import Path
from unittest.mock import patch, call
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

    @patch("zipfile.ZipFile")
    def test_create_zip(self, mock_zipfile):
        # Execute the function to create a zip file
        create_zip(self.files, self.output_path, self.temp_dir)

        # Ensure ZipFile was called correctly
        mock_zipfile.assert_called_once_with(self.output_path, "w")
        mock_zip_instance = mock_zipfile.return_value.__enter__.return_value

        # Normalize paths and build expected call list
        expected_calls = [
            call(
                os.path.normpath(str(file)),  # Normalize the full file path
                os.path.normpath(
                    file.relative_to(self.temp_dir).as_posix()
                ),  # Normalize and convert the relative path to POSIX style
            )
            for file in self.files
        ]

        # Check write call counts
        self.assertEqual(mock_zip_instance.write.call_count, len(self.files))

        # Check each expected call
        for expected in expected_calls:
            # Ensure the expected call matches the actual call using string comparison
            self.assertIn(
                call(
                    str(expected.args[0]),  # Convert WindowsPath to string
                    str(expected.args[1]),  # Convert WindowsPath to string
                ),
                [
                    call(str(actual_call.args[0]), str(actual_call.args[1]))
                    for actual_call in mock_zip_instance.write.call_args_list
                ],
                f"Expected call not found: {expected}",
            )


if __name__ == "__main__":
    unittest.main()
