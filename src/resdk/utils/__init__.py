"""ReSDK utils."""
import re


def is_email(value):
    """Check if given value looks like an email address."""
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    return re.match(email_regex, value)
