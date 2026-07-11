import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin, urlparse

import httpx

from app.core.validators import is_valid_url

# Job boards commonly 403 non-browser user agents.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# some links shouldn't be checked (LinkedIn or dummy data)
_SKIPPED_HOST_DOMAINS = ("linkedin.com",)
_SKIPPED_HOST_PREFIXES = ("dummyexample-",)

# Phrases job boards show when a posting served with HTTP 200 is actually gone.
CLOSED_PHRASES = [
    "no longer accepting applications",
    "job is no longer available",
    "job is no longer active",
    "position has been filled",
    "position is no longer open",
    "position has closed",
    "posting has expired",
    "job has expired",
    "job posting has closed",
]

# Words in a redirect target's path/query that signal the posting is gone,
# even when the rest of the URL still resembles the original.
SUSPICIOUS_URL_TOKENS = {
    "error",
    "errors",
    "404",
    "410",
    "expired",
    "redirect",
    "removed",
    "closed",
    "unavailable",
    "notfound",
}
SUSPICIOUS_URL_PHRASES = ("not found", "no longer")

MAX_REDIRECT_HOPS = 5
BODY_SNIFF_CHARS = 100_000

_META_REFRESH_RE = re.compile(
    r"<meta[^>]+http-equiv\s*=\s*[\"']?refresh[\"']?[^>]*"
    r"content\s*=\s*[\"']\s*\d+\s*;\s*url\s*=\s*([^\"'>\s]+)",
    re.IGNORECASE | re.DOTALL,
)


class Verdict(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    INCONCLUSIVE = "inconclusive"


@dataclass
class CheckResult:
    verdict: Verdict
    reason: str


def should_check(link: str | None) -> bool:
    if not link or not is_valid_url(link):
        return False
    host = (urlparse(link).hostname or "").lower()
    if host.startswith(_SKIPPED_HOST_PREFIXES):
        return False
    return not any(
        host == domain or host.endswith("." + domain) for domain in _SKIPPED_HOST_DOMAINS
    )


def _normalized(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    host = host.removeprefix("www.")
    path = parsed.path[:-1] if parsed.path.endswith("/") else parsed.path
    return (host, path, parsed.query)


def is_trivial_redirect(original_url: str, location: str) -> bool:
    """True for redirects to the same page: http->https, +/-www, +/-trailing slash."""
    return _normalized(original_url) == _normalized(location)


def _path_segments(url: str) -> list[str]:
    _, path, _ = _normalized(url)
    return [segment for segment in path.lower().split("/") if segment]


def suspicious_url_token(url: str) -> str | None:
    parsed = urlparse(url)
    tokens = [t for t in re.split(r"[^a-z0-9]+", f"{parsed.path} {parsed.query}".lower()) if t]
    bigrams = {f"{a} {b}" for a, b in zip(tokens, tokens[1:])}
    for phrase in SUSPICIOUS_URL_PHRASES:
        if phrase in bigrams:
            return phrase
    for token in tokens:
        if token in SUSPICIOUS_URL_TOKENS:
            return token
    return None


def is_same_posting(original_url: str, target_url: str) -> bool:
    """Whether a redirect target is similar enough to still be the same posting.

    The last path segment of a job URL is its identifier (id or slug); a
    redirect that keeps it (locale prefix added, job board renamed its domain)
    is followed, while one that drops it landed on a different page — an index,
    a homepage — meaning the posting itself is gone.
    """
    original_segments = _path_segments(original_url)
    if not original_segments:
        return False
    return original_segments[-1] in _path_segments(target_url)


def looks_closed_in_body(html: str) -> str | None:
    lowered = html[:BODY_SNIFF_CHARS].lower()
    for phrase in CLOSED_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def extract_meta_refresh(html: str) -> str | None:
    match = _META_REFRESH_RE.search(html[:BODY_SNIFF_CHARS])
    return match.group(1) if match else None


def _evaluate_redirect(original_url: str, target: str) -> CheckResult | None:
    """Verdict for a non-trivial redirect target; None means follow it."""
    token = suspicious_url_token(target)
    if token:
        return CheckResult(Verdict.CLOSED, f'redirected to a URL mentioning "{token}": {target}')
    if not is_same_posting(original_url, target):
        return CheckResult(Verdict.CLOSED, f"redirected to a different page: {target}")
    return None


async def check_url(client: httpx.AsyncClient, url: str) -> CheckResult:
    """Classify a job-posting URL.

    CLOSED only on definitive signals: 404/410, a redirect to a different or
    suspicious-looking page, or a 200 whose body says the posting is gone.
    Errors, timeouts, and bot-blocking responses stay INCONCLUSIVE so postings
    are never falsely closed.
    """
    current = url
    for _ in range(MAX_REDIRECT_HOPS):
        try:
            response = await client.get(current)
        except httpx.HTTPError as exc:
            return CheckResult(Verdict.INCONCLUSIVE, f"request failed: {type(exc).__name__}")

        status = response.status_code

        if 300 <= status < 400:
            location = response.headers.get("location")
            if not location:
                return CheckResult(Verdict.INCONCLUSIVE, f"HTTP {status} without Location header")
            target = urljoin(current, location)
            if not is_trivial_redirect(current, target):
                verdict = _evaluate_redirect(url, target)
                if verdict:
                    return verdict
            current = target
            continue

        if status in (404, 410):
            return CheckResult(Verdict.CLOSED, f"HTTP {status}")

        if 200 <= status < 300:
            body = response.text
            phrase = looks_closed_in_body(body)
            if phrase:
                return CheckResult(Verdict.CLOSED, f'page says "{phrase}"')
            refresh_target = extract_meta_refresh(body)
            if refresh_target:
                target = urljoin(current, refresh_target)
                if not is_trivial_redirect(current, target):
                    verdict = _evaluate_redirect(url, target)
                    if verdict:
                        return verdict
                current = target
                continue
            return CheckResult(Verdict.OPEN, f"HTTP {status}")

        return CheckResult(Verdict.INCONCLUSIVE, f"HTTP {status}")

    return CheckResult(Verdict.INCONCLUSIVE, "too many redirects")
