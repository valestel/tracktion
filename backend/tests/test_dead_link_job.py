from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.jobs import dead_link_job
from app.jobs.dead_link_job import JOB_NAME, _is_due, _record_run, run_dead_link_check
from app.models.job_run import JobRun
from app.models.status_event import StatusEvent
from app.schemas.application import ApplicationCreate
from app.services import application_service
from app.services.link_checker import CheckResult, Verdict


class TestIsDue:
    def test_due_when_never_run(self, session: Session):
        assert _is_due(session) is True

    def test_due_after_interval(self, session: Session):
        session.add(JobRun(job_name=JOB_NAME, last_run_at=datetime.utcnow() - timedelta(days=8)))
        session.commit()
        assert _is_due(session) is True

    def test_not_due_within_interval(self, session: Session):
        session.add(JobRun(job_name=JOB_NAME, last_run_at=datetime.utcnow() - timedelta(days=1)))
        session.commit()
        assert _is_due(session) is False

    def test_record_run_makes_not_due(self, session: Session):
        _record_run(session)
        assert _is_due(session) is False
        run = session.get(JobRun, JOB_NAME)
        assert run is not None


class TestRunDeadLinkCheck:
    def _make_app(self, session, company_id, title, link, status="applied"):
        return application_service.create(
            session,
            ApplicationCreate(
                company_id=company_id,
                job_title=title,
                application_date=date(2026, 6, 1),
                link=link,
                status=status,
            ),
        )

    async def test_only_dead_applied_links_are_closed(
        self, session: Session, sample_company, monkeypatch
    ):
        dead = self._make_app(session, sample_company.id, "Dead", "https://x.com/dead-job")
        live = self._make_app(session, sample_company.id, "Live", "https://x.com/live-job")
        linkedin = self._make_app(
            session, sample_company.id, "LinkedIn", "https://www.linkedin.com/jobs/view/1"
        )
        waiting = self._make_app(
            session, sample_company.id, "Waiting", "https://x.com/dead-job-2", status="waiting"
        )

        async def fake_check_url(client, url):
            if "dead" in url:
                return CheckResult(Verdict.CLOSED, "HTTP 404")
            return CheckResult(Verdict.OPEN, "HTTP 200")

        monkeypatch.setattr(dead_link_job, "check_url", fake_check_url)

        summary = await run_dead_link_check(session=session)

        assert summary == {"checked": 2, "closed": 1, "inconclusive": 0, "skipped": 1}
        assert application_service.get(session, dead.id).status == "role closed"
        assert application_service.get(session, live.id).status == "applied"
        assert application_service.get(session, linkedin.id).status == "applied"
        assert application_service.get(session, waiting.id).status == "waiting"

        events = session.exec(
            select(StatusEvent).where(StatusEvent.application_id == dead.id)
        ).all()
        assert any(e.from_status == "applied" and e.to_status == "role closed" for e in events)

    async def test_inconclusive_leaves_application_untouched(
        self, session: Session, sample_company, monkeypatch
    ):
        blocked = self._make_app(session, sample_company.id, "Blocked", "https://x.com/blocked")

        async def fake_check_url(client, url):
            return CheckResult(Verdict.INCONCLUSIVE, "HTTP 403")

        monkeypatch.setattr(dead_link_job, "check_url", fake_check_url)

        summary = await run_dead_link_check(session=session)

        assert summary == {"checked": 1, "closed": 0, "inconclusive": 1, "skipped": 0}
        assert application_service.get(session, blocked.id).status == "applied"
