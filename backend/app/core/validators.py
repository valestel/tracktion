import re
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value))


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_valid_link_or_email(value: str) -> bool:
    return is_valid_email(value) or is_valid_url(value)
