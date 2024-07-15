from urllib.parse import urlparse
from pathlib import Path
import re


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def clean_filename(filename):
    # Remove all .mp3 occurrences (case insensitive)
    cleaned = re.sub(r"\.mp3", "", filename, flags=re.IGNORECASE)

    # Remove any other file extensions
    cleaned = Path(cleaned).stem

    # Clean up remaining characters
    cleaned = "".join(c for c in cleaned if c.isalnum() or c in "._- ")

    # Add single .mp3 extension
    return cleaned
