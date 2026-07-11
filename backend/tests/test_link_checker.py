import httpx
import pytest

from app.services.link_checker import (
    Verdict,
    check_url,
    extract_meta_refresh,
    is_same_posting,
    is_trivial_redirect,
    looks_closed_in_body,
    should_check,
    suspicious_url_token,
)


def make_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


class TestShouldCheck:
    def test_none_link(self):
        assert should_check(None) is False

    def test_empty_link(self):
        assert should_check("") is False

    def test_email_link(self):
        assert should_check("recruiter@company.com") is False

    def test_not_a_url(self):
        assert should_check("just some text") is False

    def test_linkedin(self):
        assert should_check("https://linkedin.com/jobs/view/123") is False

    def test_linkedin_subdomain(self):
        assert should_check("https://www.linkedin.com/jobs/view/123") is False

    def test_dummy_data_link(self):
        assert should_check("https://dummyexample-acmecorp.com/careers/3") is False

    def test_regular_url(self):
        assert should_check("https://boards.greenhouse.io/acme/jobs/123") is True

    def test_lookalike_host_is_checked(self):
        assert should_check("https://notlinkedin.com/jobs/1") is True


class TestIsTrivialRedirect:
    @pytest.mark.parametrize(
        "original,location",
        [
            ("http://example.com/job/1", "https://example.com/job/1"),
            ("https://example.com/job/1", "https://www.example.com/job/1"),
            ("https://www.example.com/job/1", "https://example.com/job/1"),
            ("https://example.com/job/1", "https://example.com/job/1/"),
            ("http://example.com/job/1", "https://www.example.com/job/1/"),
        ],
    )
    def test_trivial(self, original, location):
        assert is_trivial_redirect(original, location) is True

    @pytest.mark.parametrize(
        "original,location",
        [
            ("https://example.com/job/1", "https://example.com/jobs"),
            ("https://example.com/job/1", "https://other.com/job/1"),
            ("https://example.com/job/1", "https://example.com/job/1?expired=true"),
            ("https://jobs.example.com/1", "https://careers.example.com/1"),
        ],
    )
    def test_not_trivial(self, original, location):
        assert is_trivial_redirect(original, location) is False


class TestSuspiciousUrlToken:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://x.com/jobs/expired", "expired"),
            ("https://x.com/error/404", "error"),
            ("https://x.com/careers/job-not-found", "not found"),
            ("https://x.com/jobs/123?state=closed", "closed"),
            ("https://x.com/redirect?to=home", "redirect"),
        ],
    )
    def test_suspicious(self, url, expected):
        assert suspicious_url_token(url) == expected

    @pytest.mark.parametrize(
        "url",
        [
            "https://x.com/jobs/senior-engineer-1234",
            "https://x.com/en/careers/apply/9876",
            # "notorious" must not match "not" + suspicious bigram splitting
            "https://x.com/jobs/notorious-founders-assistant",
        ],
    )
    def test_normal_urls_not_flagged(self, url):
        assert suspicious_url_token(url) is None


class TestIsSamePosting:
    @pytest.mark.parametrize(
        "original,target",
        [
            # locale prefix added
            ("https://x.com/jobs/engineer-123", "https://x.com/en-us/jobs/engineer-123"),
            # job board renamed its domain
            (
                "https://boards.greenhouse.io/acme/jobs/42",
                "https://job-boards.greenhouse.io/acme/jobs/42",
            ),
            # URL structure reshuffled but identifier kept
            ("https://x.com/careers/123", "https://x.com/jobs/openings/123"),
        ],
    )
    def test_same_posting(self, original, target):
        assert is_same_posting(original, target) is True

    @pytest.mark.parametrize(
        "original,target",
        [
            # bounced to the jobs index
            ("https://x.com/job/123", "https://x.com/jobs"),
            # bounced to the homepage
            ("https://x.com/jobs/engineer-123", "https://x.com/"),
            # a different posting
            ("https://x.com/jobs/123", "https://x.com/jobs/456"),
        ],
    )
    def test_different_page(self, original, target):
        assert is_same_posting(original, target) is False


class TestBodySniffing:
    def test_closed_phrase_found(self):
        html = "<html><body><p>This job is no longer accepting applications.</p></body></html>"
        assert looks_closed_in_body(html) == "no longer accepting applications"

    def test_closed_phrase_case_insensitive(self):
        assert looks_closed_in_body("THE POSITION HAS BEEN FILLED") == "position has been filled"

    def test_open_page(self):
        assert looks_closed_in_body("<html><body>Apply now!</body></html>") is None

    def test_meta_refresh_extracted(self):
        html = '<meta http-equiv="refresh" content="0;url=https://example.com/careers">'
        assert extract_meta_refresh(html) == "https://example.com/careers"

    def test_meta_refresh_absent(self):
        assert extract_meta_refresh("<html><body>hi</body></html>") is None


class TestCheckUrl:
    async def test_200_plain_is_open(self):
        async with make_client(lambda req: httpx.Response(200, text="<h1>Apply now</h1>")) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.OPEN

    async def test_200_with_closed_phrase_is_closed(self):
        html = "<p>This job is no longer available.</p>"
        async with make_client(lambda req: httpx.Response(200, text=html)) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.CLOSED
        assert "no longer available" in result.reason

    async def test_200_with_meta_refresh_to_other_page_is_closed(self):
        html = '<meta http-equiv="refresh" content="0;url=https://example.com/careers">'
        async with make_client(lambda req: httpx.Response(200, text=html)) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.CLOSED

    @pytest.mark.parametrize("status", [404, 410])
    async def test_gone_is_closed(self, status):
        async with make_client(lambda req: httpx.Response(status)) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.CLOSED
        assert str(status) in result.reason

    async def test_redirect_to_other_page_is_closed(self):
        def handler(request):
            return httpx.Response(302, headers={"location": "https://example.com/jobs"})

        async with make_client(handler) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.CLOSED
        assert "redirected" in result.reason

    async def test_redirect_keeping_identifier_is_followed(self):
        def handler(request):
            if "/en/" not in request.url.path:
                return httpx.Response(
                    302, headers={"location": "https://example.com/en/jobs/engineer-123"}
                )
            return httpx.Response(200, text="<h1>Apply now</h1>")

        async with make_client(handler) as client:
            result = await check_url(client, "https://example.com/jobs/engineer-123")
        assert result.verdict is Verdict.OPEN

    async def test_redirect_to_suspicious_url_is_closed_even_if_similar(self):
        def handler(request):
            return httpx.Response(
                302, headers={"location": "https://example.com/jobs/engineer-123?error=expired"}
            )

        async with make_client(handler) as client:
            result = await check_url(client, "https://example.com/jobs/engineer-123")
        assert result.verdict is Verdict.CLOSED
        assert "error" in result.reason

    async def test_meta_refresh_keeping_identifier_is_followed(self):
        def handler(request):
            if "/en/" not in request.url.path:
                html = '<meta http-equiv="refresh" content="0;url=https://example.com/en/jobs/engineer-123">'
                return httpx.Response(200, text=html)
            return httpx.Response(200, text="<h1>Apply now</h1>")

        async with make_client(handler) as client:
            result = await check_url(client, "https://example.com/jobs/engineer-123")
        assert result.verdict is Verdict.OPEN

    async def test_trivial_redirect_is_followed(self):
        def handler(request):
            if request.url.scheme == "http":
                return httpx.Response(301, headers={"location": "https://example.com/job/1"})
            return httpx.Response(200, text="<h1>Apply now</h1>")

        async with make_client(handler) as client:
            result = await check_url(client, "http://example.com/job/1")
        assert result.verdict is Verdict.OPEN

    async def test_trivial_redirect_loop_is_inconclusive(self):
        def handler(request):
            if request.url.host == "example.com":
                return httpx.Response(301, headers={"location": "https://www.example.com/job/1"})
            return httpx.Response(301, headers={"location": "https://example.com/job/1"})

        async with make_client(handler) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.INCONCLUSIVE

    async def test_timeout_is_inconclusive(self):
        def handler(request):
            raise httpx.ConnectTimeout("timed out")

        async with make_client(handler) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.INCONCLUSIVE

    @pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
    async def test_blocked_or_error_is_inconclusive(self, status):
        async with make_client(lambda req: httpx.Response(status)) as client:
            result = await check_url(client, "https://example.com/job/1")
        assert result.verdict is Verdict.INCONCLUSIVE
