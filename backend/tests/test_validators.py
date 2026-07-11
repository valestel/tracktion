from app.core.validators import is_valid_email, is_valid_link_or_email, is_valid_url


def test_is_valid_email_accepts_standard_email():
    assert is_valid_email("jobs@example-company.com")


def test_is_valid_email_rejects_missing_at():
    assert not is_valid_email("example-company.com")


def test_is_valid_email_rejects_missing_domain_dot():
    assert not is_valid_email("jobs@example")


def test_is_valid_url_accepts_http_and_https():
    assert is_valid_url("http://example.com/jobs")
    assert is_valid_url("https://example.com/jobs")


def test_is_valid_url_rejects_missing_scheme():
    assert not is_valid_url("example.com/jobs")


def test_is_valid_url_rejects_non_http_scheme():
    assert not is_valid_url("ftp://example.com/jobs")


def test_is_valid_link_or_email_accepts_either_format():
    assert is_valid_link_or_email("jobs@example-company.com")
    assert is_valid_link_or_email("https://example.com/careers")


def test_is_valid_link_or_email_rejects_bare_domain():
    assert not is_valid_link_or_email("example-company.com/jobs")


def test_is_valid_link_or_email_rejects_malformed_concatenation():
    # The original bug report: a path-like local part before "@" (e.g. one
    # that already contains a host/port/slash) must not be treated as a
    # valid email, or the frontend would resolve it relative to its own
    # origin as "localhost:8000/jobs@example-company.com".
    assert not is_valid_link_or_email("localhost:8000/jobs@example-company.com")
