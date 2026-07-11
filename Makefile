.PHONY: dev

dev:
	@trap 'kill 0' EXIT; \
	(cd backend && uv run uvicorn app.main:app --reload --timeout-graceful-shutdown 3) & \
	(cd frontend && npm run dev) & \
	wait
