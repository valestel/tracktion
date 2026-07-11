from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRACKTION_", env_file=".env", extra="ignore")

    db_path: str = "../data/tracktion.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    default_statuses: list[tuple[str, str, int]] = [
        # (name, hex_color, sort_order)
        ("applied", "#60a5fa", 0),
        ("screen/intro", "#a78bfa", 1),
        ("take-home task", "#fb923c", 2),
        ("tech interview", "#f59e0b", 3),
        ("culture interview", "#e879f9", 4),
        ("offer", "#4ade80", 5),
        ("rejected", "#f87171", 6),
        ("ghosted", "#64748b", 7),
        ("withdrawn", "#94a3b8", 8),
        ("waiting", "#e2e8f0", 9),
        ("role closed", "#cfae80", 10),
    ]
    # Statuses that are transitional holding states, not funnel stages:
    # excluded from analytics (collapsed out of sankey chains, funnel counts
    # the application under its last substantive status instead).
    transitional_statuses: list[str] = ["waiting"]

    # Weekly dead-link check job
    link_check_interval_days: int = 7
    link_check_poll_seconds: int = 3600
    link_check_concurrency: int = 5
    link_check_timeout_seconds: float = 10.0


settings = Settings()
