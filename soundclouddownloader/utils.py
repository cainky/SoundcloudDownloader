from urllib.parse import urlparse
from pathlib import Path
from unidecode import unidecode
import re, zipfile
from loguru import logger
from typing import List


def validate_url(url: str) -> bool:
    """
    Validate if the given string is a valid URL.

    This function checks if the input string has both a scheme (e.g., http, https)
    and a network location (e.g., www.example.com).

    Args:
        url (str): The URL string to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def clean_filename(filename: str) -> str:
    """
    Clean a filename by removing or replacing invalid characters.

    This function:
    1. Transliterates Unicode characters to their ASCII equivalents
    2. Removes or replaces characters that are typically invalid in filenames
    3. Ensures the filename doesn't exceed a maximum length

    Args:
        filename (str): The original filename to clean.

    Returns:
        str: The cleaned filename.
    """
    # Transliterate Unicode characters to ASCII
    filename = unidecode(filename)

    # Replace spaces and dots with underscores, except the last dot (extension)
    filename = re.sub(r"[\s.]+(?=.*\.)", "_", filename)

    # Remove or replace special characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)

    # Replace multiple consecutive underscores with a single underscore
    filename = re.sub(r"_{2,}", "_", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")

    # Limit filename length (255 is a common max length, adjust if needed)
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[: max_length - len(ext)] + ext
    return filename


def create_zip(files: List[Path], zip_filename: Path, source_dir: Path) -> None:
    """
    Create a zip file containing the downloaded tracks.

    Args:
        files (List[Path]): List of files to be included in the zip.
        zip_filename (Path): Path where the zip file will be created.
        source_dir (Path): The directory containing the files to be zipped.
    """
    logger.debug(f"Creating zip file: {zip_filename}")
    logger.debug(f"Files to be zipped: {files}")

    logger.info("Zipping files now please wait...")
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for file in files:
            if file.exists():
                logger.debug(f"Adding file to zip: {file}")
                arcname = file.relative_to(source_dir)
                zipf.write(file, arcname)
            else:
                logger.warning(f"File not found when creating zip: {file}")
