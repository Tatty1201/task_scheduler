from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.task_mapper import build_event_payload


def _task(limit_type: str, limit_time: int = 0) -> dict:
    return {
        "task_id": 42,
        "room": {"room_id": 7, "name": "Project"},
        "assigned_by_account": {"name": "Alice"},
        "message_id": "99",
        "body": "Prepare weekly report",
        "limit_type": limit_type,
        "limit_time": limit_time,
    }


def test_time_limit_uses_exact_deadline() -> None:
    tz = ZoneInfo("Asia/Tokyo")
    deadline = int(datetime(2026, 8, 20, 14, 30, tzinfo=tz).timestamp())

    payload = build_event_payload(
        task=_task("time", deadline),
        account_name="main",
        send_time=None,
        timezone_name="Asia/Tokyo",
        default_start_time="10:00",
        duration_min=60,
    )

    assert payload["start"]["dateTime"].startswith("2026-08-20T14:30:00")
    assert payload["end"]["dateTime"].startswith("2026-08-20T15:30:00")
    assert payload["extendedProperties"]["private"]["chatwork_task_key"] == "main:42"


def test_no_deadline_uses_message_date_and_default_time() -> None:
    tz = ZoneInfo("Asia/Tokyo")
    send_time = int(datetime(2026, 8, 18, 21, 15, tzinfo=tz).timestamp())

    payload = build_event_payload(
        task=_task("none"),
        account_name="main",
        send_time=send_time,
        timezone_name="Asia/Tokyo",
        default_start_time="09:30",
        duration_min=45,
    )

    assert payload["start"]["dateTime"].startswith("2026-08-18T09:30:00")
    assert payload["end"]["dateTime"].startswith("2026-08-18T10:15:00")
