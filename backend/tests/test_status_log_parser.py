from datetime import date, datetime

from app.core.status_log_parser import (
    ParsedStatusEntry,
    build_event_chain,
    parse_log_date,
    parse_status_log,
)

KNOWN = ["applied", "screening call", "tech interview", "interview", "offer", "rejected"]


def test_parse_log_date_uses_year_hint():
    assert parse_log_date("4.06", 2026) == date(2026, 6, 4)


def test_parse_log_date_explicit_year_ignores_hint():
    assert parse_log_date("4.6.2025", 2026) == date(2025, 6, 4)


def test_parse_log_date_invalid_day_month_returns_none():
    assert parse_log_date("31.4", 2026) is None


def test_parse_log_date_two_digit_year_rejected():
    assert parse_log_date("4.6.26", 2026) is None


def test_parse_log_date_garbage_returns_none():
    assert parse_log_date("abc", 2026) is None
    assert parse_log_date("4", 2026) is None
    assert parse_log_date("", 2026) is None


def test_parse_status_log_example_string():
    notes = "4.06 - screening call, 12.06 - tech interview"
    result = parse_status_log(notes, date(2026, 1, 5), KNOWN)
    assert result.entries == [
        ParsedStatusEntry(date=date(2026, 6, 4), to_status="screening call"),
        ParsedStatusEntry(date=date(2026, 6, 12), to_status="tech interview"),
    ]
    assert result.unrecognized == []


def test_parse_status_log_sorts_out_of_order_entries():
    notes = "12.06 - tech interview, 4.06 - screening call"
    result = parse_status_log(notes, date(2026, 1, 5), KNOWN)
    assert [e.date for e in result.entries] == [date(2026, 6, 4), date(2026, 6, 12)]


def test_parse_status_log_reports_unknown_status_as_unrecognized():
    notes = "4.06 - screening call, 12.06 - some unknown thing"
    result = parse_status_log(notes, date(2026, 1, 5), KNOWN)
    assert len(result.entries) == 1
    assert result.entries[0].to_status == "screening call"
    assert result.unrecognized == ["12.06 - some unknown thing"]


def test_parse_status_log_plain_text_is_not_unrecognized():
    # Free text without the "date - status" shape is normal notes, no warning
    notes = "not a real entry, 4.06 - applied"
    result = parse_status_log(notes, date(2026, 1, 5), KNOWN)
    assert len(result.entries) == 1
    assert result.entries[0].to_status == "applied"
    assert result.unrecognized == []


def test_parse_status_log_invalid_date_is_unrecognized():
    notes = "31.4 - screening call"
    result = parse_status_log(notes, date(2026, 1, 5), KNOWN)
    assert result.entries == []
    assert result.unrecognized == ["31.4 - screening call"]


def test_parse_status_log_empty_or_none_notes():
    assert parse_status_log(None, date(2026, 1, 5), KNOWN).entries == []
    assert parse_status_log("", date(2026, 1, 5), KNOWN).entries == []
    assert parse_status_log("   ", date(2026, 1, 5), KNOWN).entries == []


def test_parse_status_log_duplicate_dates_stable_order():
    notes = "4.06 - screening call, 4.06 - tech interview"
    result = parse_status_log(notes, date(2026, 1, 5), KNOWN)
    assert [e.to_status for e in result.entries] == ["screening call", "tech interview"]


APP_DATE = date(2026, 1, 5)


def test_build_event_chain_no_initial_no_entries_falls_back_to_single_event():
    chain = build_event_chain([], "applied", APP_DATE)
    assert len(chain) == 1
    assert chain[0].from_status is None
    assert chain[0].to_status == "applied"
    assert chain[0].timestamp is None


def test_build_event_chain_starts_at_initial_status_on_application_date():
    chain = build_event_chain([], "applied", APP_DATE, initial_status="applied")
    assert len(chain) == 1
    assert chain[0].from_status is None
    assert chain[0].to_status == "applied"
    assert chain[0].timestamp == datetime(2026, 1, 5)


def test_build_event_chain_final_status_diverging_from_initial_appends_catchup():
    chain = build_event_chain([], "rejected", APP_DATE, initial_status="applied")
    assert len(chain) == 2
    assert chain[0].to_status == "applied"
    assert chain[0].timestamp == datetime(2026, 1, 5)
    assert chain[1].from_status == "applied"
    assert chain[1].to_status == "rejected"
    assert chain[1].timestamp is None


def test_build_event_chain_matching_final_status_no_catchup():
    entries = [
        ParsedStatusEntry(date=date(2026, 6, 4), to_status="screening call"),
        ParsedStatusEntry(date=date(2026, 6, 12), to_status="tech interview"),
    ]
    chain = build_event_chain(entries, "tech interview", APP_DATE, initial_status="applied")
    assert len(chain) == 3
    assert chain[0].from_status is None
    assert chain[0].to_status == "applied"
    assert chain[0].timestamp == datetime(2026, 1, 5)
    assert chain[1].from_status == "applied"
    assert chain[1].to_status == "screening call"
    assert chain[1].timestamp == datetime(2026, 6, 4)
    assert chain[2].from_status == "screening call"
    assert chain[2].to_status == "tech interview"
    assert chain[2].timestamp == datetime(2026, 6, 12)


def test_build_event_chain_diverging_final_status_appends_catchup():
    entries = [ParsedStatusEntry(date=date(2026, 6, 4), to_status="screening call")]
    chain = build_event_chain(entries, "offer", APP_DATE, initial_status="applied")
    assert len(chain) == 3
    assert chain[2].from_status == "screening call"
    assert chain[2].to_status == "offer"
    assert chain[2].timestamp is None


def test_build_event_chain_skips_noop_transition():
    # A log entry repeating the current status must not create applied -> applied
    entries = [ParsedStatusEntry(date=date(2026, 6, 4), to_status="applied")]
    chain = build_event_chain(entries, "applied", APP_DATE, initial_status="applied")
    assert len(chain) == 1
    assert chain[0].to_status == "applied"
