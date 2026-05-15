"""Chatworkタスク → Googleカレンダーイベントへの変換ロジック。"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .google_calendar import TASK_KEY_PROPERTY, make_task_key


# カレンダー予定のタイトル最大長 (ルーム名プレフィックス含む)
TITLE_MAX_LEN = 100
BODY_MAX_LEN = 80


def _parse_default_time(default_start_time: str) -> tuple[int, int]:
    """'HH:MM' → (hour, minute)。"""
    hour_str, minute_str = default_start_time.split(":", 1)
    return int(hour_str), int(minute_str)


def _build_title(room_name: str, body: str) -> str:
    """`[ルーム名] タスク本文(先頭80文字)` 形式のタイトル。アカウント名は含めない。"""
    one_line_body = body.replace("\n", " ").strip()
    if len(one_line_body) > BODY_MAX_LEN:
        one_line_body = one_line_body[:BODY_MAX_LEN] + "…"
    title = f"[{room_name}] {one_line_body}"
    if len(title) > TITLE_MAX_LEN:
        title = title[:TITLE_MAX_LEN] + "…"
    return title


def _build_description(
    task: dict[str, Any],
    send_time: int | None,
    tz: ZoneInfo,
) -> str:
    """説明欄テキストを生成。"""
    assigned_by = task.get("assigned_by_account") or {}
    assigned_by_name = assigned_by.get("name", "不明")

    room = task.get("room") or {}
    room_id = room.get("room_id")
    message_id = task.get("message_id")

    lines: list[str] = [
        f"依頼者: {assigned_by_name}",
    ]
    if send_time:
        registered_at = datetime.fromtimestamp(send_time, tz=tz)
        lines.append(
            f"登録日時: {registered_at.strftime('%Y-%m-%d %H:%M')}"
        )
    if room_id and message_id:
        lines.append(
            f"Chatworkで開く: https://www.chatwork.com/#!rid{room_id}-{message_id}"
        )
    lines.append(f"task_id: {task.get('task_id')}")
    return "\n".join(lines)


def _compute_datetime_range(
    task: dict[str, Any],
    send_time: int | None,
    tz: ZoneInfo,
    default_start_time: str,
    duration_min: int,
) -> tuple[datetime, datetime]:
    """limit_type に応じて (start, end) を計算する。

    - time : 期限時刻 〜 +duration_min
    - date : 期限当日の default_start_time 〜 +duration_min
    - none : 登録日 (send_time) の default_start_time 〜 +duration_min
    """
    limit_type = task.get("limit_type", "none")
    limit_time = task.get("limit_time", 0) or 0

    default_h, default_m = _parse_default_time(default_start_time)

    if limit_type == "time" and limit_time:
        start = datetime.fromtimestamp(limit_time, tz=tz)
    elif limit_type == "date" and limit_time:
        base = datetime.fromtimestamp(limit_time, tz=tz)
        start = base.replace(
            hour=default_h, minute=default_m, second=0, microsecond=0
        )
    else:
        # limit_type == "none" もしくは limit_time が無効 → 登録日基準
        if not send_time:
            raise ValueError(
                f"limit_type={limit_type} だが send_time も無く日時を決定できません"
                f" (task_id={task.get('task_id')})"
            )
        base = datetime.fromtimestamp(send_time, tz=tz)
        start = base.replace(
            hour=default_h, minute=default_m, second=0, microsecond=0
        )

    end = start + timedelta(minutes=duration_min)
    return start, end


def build_event_payload(
    task: dict[str, Any],
    account_name: str,
    send_time: int | None,
    timezone_name: str,
    default_start_time: str,
    duration_min: int,
) -> dict[str, Any]:
    """Chatworkタスク (+ account_name + send_time) から events.insert 用 body を作る。"""
    tz = ZoneInfo(timezone_name)
    room = task.get("room") or {}
    room_name = room.get("name", "不明ルーム")
    body = task.get("body", "")
    task_id = int(task["task_id"])

    start, end = _compute_datetime_range(
        task, send_time, tz, default_start_time, duration_min
    )

    return {
        "summary": _build_title(room_name, body),
        "description": _build_description(task, send_time, tz),
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": timezone_name,
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": timezone_name,
        },
        "extendedProperties": {
            "private": {
                TASK_KEY_PROPERTY: make_task_key(account_name, task_id),
            }
        },
    }


def needs_send_time(task: dict[str, Any]) -> bool:
    """このタスクの登録に send_time の取得が必須か？

    limit_type=none のタスクは start を決めるために send_time が必須。
    それ以外は説明欄用なので無くても登録は可能（だが付けたほうが情報量が増える）。
    """
    limit_type = task.get("limit_type", "none")
    limit_time = task.get("limit_time", 0) or 0
    if limit_type == "none":
        return True
    if not limit_time:
        # limit_type が time/date でも 0 なら none 相当
        return True
    return False
