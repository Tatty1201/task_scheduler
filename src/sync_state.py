"""同期状態を SQLite に保存するモジュール。

複数Chatworkアカウント対応のため `(account_name, task_id)` を複合主キーにする。

スキーマ:
    task_events(
        account_name TEXT    NOT NULL,
        task_id      INTEGER NOT NULL,
        room_id      INTEGER NOT NULL,
        event_id     TEXT    NOT NULL,
        synced_at    TEXT    NOT NULL,
        PRIMARY KEY (account_name, task_id)
    )
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS task_events (
    account_name TEXT    NOT NULL,
    task_id      INTEGER NOT NULL,
    room_id      INTEGER NOT NULL,
    event_id     TEXT    NOT NULL,
    synced_at    TEXT    NOT NULL,
    PRIMARY KEY (account_name, task_id)
);
"""


class SyncStateStore:
    """(account_name, task_id) ↔ event_id の永続化。"""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def is_synced(self, account_name: str, task_id: int) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM task_events WHERE account_name = ? AND task_id = ?",
            (account_name, task_id),
        )
        return cur.fetchone() is not None

    def get_event_id(self, account_name: str, task_id: int) -> str | None:
        cur = self._conn.execute(
            "SELECT event_id FROM task_events"
            " WHERE account_name = ? AND task_id = ?",
            (account_name, task_id),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def save(
        self,
        account_name: str,
        task_id: int,
        room_id: int,
        event_id: str,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO task_events
                (account_name, task_id, room_id, event_id, synced_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(account_name, task_id) DO UPDATE SET
                room_id   = excluded.room_id,
                event_id  = excluded.event_id,
                synced_at = excluded.synced_at
            """,
            (account_name, task_id, room_id, event_id, now_iso),
        )
        self._conn.commit()

    def reset(self) -> None:
        """全レコード削除（カレンダー側のイベントは消さない）。"""
        self._conn.execute("DELETE FROM task_events")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SyncStateStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
