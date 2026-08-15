from __future__ import annotations

from src.sync_state import SyncStateStore


def test_same_task_id_can_exist_in_multiple_accounts(tmp_path) -> None:
    db_path = tmp_path / "state.db"

    with SyncStateStore(db_path) as store:
        store.save("main", 123, 1, "event-main")
        store.save("client_a", 123, 2, "event-client")

        assert store.is_synced("main", 123)
        assert store.is_synced("client_a", 123)
        assert store.get_event_id("main", 123) == "event-main"
        assert store.get_event_id("client_a", 123) == "event-client"


def test_reset_clears_sync_state(tmp_path) -> None:
    db_path = tmp_path / "state.db"

    with SyncStateStore(db_path) as store:
        store.save("main", 1, 1, "event-1")
        store.reset()
        assert not store.is_synced("main", 1)
