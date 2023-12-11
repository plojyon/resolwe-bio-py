"""ReSDK utils."""

import hashlib
import pathlib
import re
from typing import Union


def is_email(value):
    """Check if given value looks like an email address."""
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    return re.match(email_regex, value)


def md5(
    path: Union[str, pathlib.Path],
    chunk_size: int = 10 * 1024**2,
) -> str:
    """Get the md5 checksum of a file."""
    hash = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hash.update(chunk)

    return hash.hexdigest()
