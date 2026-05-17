from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_time(value: str | None) -> datetime:
    if not value:
        return utc_now()
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
