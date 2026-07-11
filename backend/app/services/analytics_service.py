from collections import Counter

from sqlmodel import Session, select

from app.config import settings
from app.models.application import Application
from app.models.status import Status
from app.repositories import status_event_repo
from app.schemas.analytics import FunnelData, FunnelStage, SankeyData, SankeyLink, SankeyNode, StatusEventRead


def _substantive_chains(session: Session) -> dict[int, list[str]]:
    """Per-application ordered status chains with transitional statuses removed.

    Collapsing e.g. applied -> waiting -> interview into applied -> interview,
    and applied -> waiting -> applied into just applied.
    """
    transitional = set(settings.transitional_statuses)
    chains: dict[int, list[str]] = {}
    for event in status_event_repo.list_all_ordered(session):
        chain = chains.setdefault(event.application_id, [])
        if event.to_status in transitional:
            continue
        if chain and chain[-1] == event.to_status:
            continue
        chain.append(event.to_status)
    return chains


def get_sankey(session: Session) -> SankeyData:
    chains = _substantive_chains(session)

    node_names: set[str] = set()
    link_counts: Counter[tuple[str, str]] = Counter()
    for chain in chains.values():
        node_names.update(chain)
        for from_s, to_s in zip(chain, chain[1:]):
            link_counts[(from_s, to_s)] += 1

    nodes = [SankeyNode(id=n, name=n) for n in sorted(node_names)]
    links = [
        SankeyLink(source=from_s, target=to_s, value=count)
        for (from_s, to_s), count in sorted(link_counts.items())
    ]
    return SankeyData(nodes=nodes, links=links)


def get_funnel(session: Session) -> FunnelData:
    transitional = set(settings.transitional_statuses)
    status_order = {
        s.name: s.sort_order
        for s in session.exec(select(Status)).all()
    }

    stmt = select(Application).where(Application.archived_at.is_(None))  # type: ignore[union-attr]
    apps = session.exec(stmt).all()

    # Applications sitting in a transitional status still belong to their
    # last substantive stage for funnel purposes.
    chains = (
        _substantive_chains(session)
        if any(a.status in transitional for a in apps)
        else {}
    )

    counts: Counter[str] = Counter()
    for app in apps:
        status = app.status
        if status in transitional:
            chain = chains.get(app.id) or []
            if not chain:
                continue
            status = chain[-1]
        counts[status] += 1

    stages = sorted(
        [FunnelStage(name=name, count=count) for name, count in counts.items()],
        key=lambda s: status_order.get(s.name, 999),
    )
    return FunnelData(stages=stages)


def get_timeline(session: Session, application_id: int) -> list[StatusEventRead]:
    events = status_event_repo.list_for_application(session, application_id)
    return [
        StatusEventRead(
            id=e.id,  # type: ignore[arg-type]
            application_id=e.application_id,
            from_status=e.from_status,
            to_status=e.to_status,
            timestamp=e.timestamp.isoformat(),
            note=e.note,
        )
        for e in events
    ]
