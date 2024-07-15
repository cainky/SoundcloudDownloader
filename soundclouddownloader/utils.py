from urllib.parse import urlparse
from pathlib import Path
import re


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

    This function removes all characters from the filename except for
    alphanumeric characters, dots, underscores, hyphens, and spaces.

    Args:
        filename (str): The original filename to clean.

    Returns:
        str: The cleaned filename.
    """

    cleaned = "".join(c for c in filename if c.isalnum() or c in "._- ")
    return cleaned
