from datetime import date

from sqlmodel import Session

from app.models.status import Status
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services import analytics_service, application_service


def _seed_statuses(session: Session):
    statuses = [
        ("applied", 0), ("interview", 1), ("offer", 2), ("rejected", 3), ("waiting", 4)
    ]
    for name, order in statuses:
        session.add(Status(name=name, color=None, sort_order=order))
    session.commit()


def _make_app(session, company, title, status="applied"):
    data = ApplicationCreate(
        company_id=company.id,
        job_title=title,
        application_date=date(2026, 1, 1),
        status=status,
    )
    return application_service.create(session, data)


def test_sankey_builds_nodes_and_links(session: Session, sample_company):
    _seed_statuses(session)
    app = _make_app(session, sample_company, "SWE")
    application_service.update(session, app.id, ApplicationUpdate(status="interview"))
    application_service.update(session, app.id, ApplicationUpdate(status="offer"))

    sankey = analytics_service.get_sankey(session)
    node_names = {n.name for n in sankey.nodes}
    assert "applied" in node_names
    assert "interview" in node_names
    assert "offer" in node_names

    link_pairs = {(link.source, link.target) for link in sankey.links}
    assert ("applied", "interview") in link_pairs
    assert ("interview", "offer") in link_pairs


def test_sankey_link_values_reflect_counts(session: Session, sample_company):
    _seed_statuses(session)
    for i in range(3):
        app = _make_app(session, sample_company, f"Role {i}")
        application_service.update(session, app.id, ApplicationUpdate(status="interview"))

    sankey = analytics_service.get_sankey(session)
    link = next(link for link in sankey.links if link.source == "applied" and link.target == "interview")
    assert link.value == 3


def test_sankey_collapses_waiting(session: Session, sample_company):
    _seed_statuses(session)
    app = _make_app(session, sample_company, "SWE")
    application_service.update(session, app.id, ApplicationUpdate(status="waiting"))
    application_service.update(session, app.id, ApplicationUpdate(status="interview"))

    sankey = analytics_service.get_sankey(session)
    node_names = {n.name for n in sankey.nodes}
    assert "waiting" not in node_names

    link_pairs = {(link.source, link.target) for link in sankey.links}
    assert link_pairs == {("applied", "interview")}


def test_sankey_waiting_round_trip_yields_no_link(session: Session, sample_company):
    _seed_statuses(session)
    app = _make_app(session, sample_company, "SWE")
    application_service.update(session, app.id, ApplicationUpdate(status="waiting"))
    application_service.update(session, app.id, ApplicationUpdate(status="applied"))

    sankey = analytics_service.get_sankey(session)
    assert sankey.links == []


def test_funnel_counts_waiting_app_under_last_real_status(session: Session, sample_company):
    _seed_statuses(session)
    app = _make_app(session, sample_company, "SWE")
    application_service.update(session, app.id, ApplicationUpdate(status="interview"))
    application_service.update(session, app.id, ApplicationUpdate(status="waiting"))

    funnel = analytics_service.get_funnel(session)
    counts = {s.name: s.count for s in funnel.stages}
    assert "waiting" not in counts
    assert counts["interview"] == 1


def test_funnel_skips_app_that_was_only_ever_waiting(session: Session, sample_company):
    _seed_statuses(session)
    _make_app(session, sample_company, "SWE", status="waiting")

    funnel = analytics_service.get_funnel(session)
    assert funnel.stages == []


def test_funnel_counts_active_by_status(session: Session, sample_company):
    _seed_statuses(session)
    _make_app(session, sample_company, "A", status="applied")
    _make_app(session, sample_company, "B", status="applied")
    _make_app(session, sample_company, "C", status="interview")

    # Archive one to confirm it's excluded
    app = _make_app(session, sample_company, "D", status="applied")
    application_service.archive(session, app.id)

    funnel = analytics_service.get_funnel(session)
    counts = {s.name: s.count for s in funnel.stages}
    assert counts["applied"] == 2
    assert counts["interview"] == 1
    assert "D" not in str(counts)  # archived not counted


def test_funnel_ordered_by_sort_order(session: Session, sample_company):
    _seed_statuses(session)
    _make_app(session, sample_company, "X", status="offer")
    _make_app(session, sample_company, "Y", status="applied")

    funnel = analytics_service.get_funnel(session)
    names = [s.name for s in funnel.stages]
    assert names.index("applied") < names.index("offer")


def test_timeline_returns_ordered_events(session: Session, sample_company):
    _seed_statuses(session)
    app = _make_app(session, sample_company, "Timeline Test")
    application_service.update(session, app.id, ApplicationUpdate(status="interview"))
    application_service.update(session, app.id, ApplicationUpdate(status="rejected"))

    timeline = analytics_service.get_timeline(session, app.id)
    assert len(timeline) == 3
    statuses = [e.to_status for e in timeline]
    assert statuses == ["applied", "interview", "rejected"]
