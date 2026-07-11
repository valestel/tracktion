"""Check job-posting URL(s) with the same logic the weekly dead-link job uses.

Usage: uv run python scripts/check_link.py <url> [<url> ...]
"""
import asyncio
import sys

import httpx

from app.config import settings
from app.services.link_checker import USER_AGENT, check_url, should_check


async def main(urls: list[str]) -> None:
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=settings.link_check_timeout_seconds,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        for url in urls:
            print(url)
            if not should_check(url):
                print("  verdict: skipped (empty, email, invalid, or LinkedIn URL)")
                continue
            result = await check_url(client, url)
            print(f"  verdict: {result.verdict.value}")
            print(f"  reason:  {result.reason}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1:]))
