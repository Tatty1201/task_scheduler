from __future__ import annotations

from typing import Any

from src.chatwork_client import ChatworkClient


class FakeResponse:
    def __init__(self, status_code: int, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        if self.status_code == 204:
            raise AssertionError("json() must not be called for 204 responses")
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response

    def get(self, *args: Any, **kwargs: Any) -> FakeResponse:
        return self.response


def test_list_my_tasks_returns_empty_list_for_204() -> None:
    client = ChatworkClient("dummy-token")
    client._session = FakeSession(FakeResponse(204))  # type: ignore[assignment]

    assert client.list_my_tasks() == []


def test_list_my_tasks_returns_payload_for_200() -> None:
    payload = [{"task_id": 1, "body": "test"}]
    client = ChatworkClient("dummy-token")
    client._session = FakeSession(FakeResponse(200, payload))  # type: ignore[assignment]

    assert client.list_my_tasks() == payload
