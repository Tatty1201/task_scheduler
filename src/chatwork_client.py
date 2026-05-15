"""Chatwork API の薄いラッパー。

ドキュメント: https://developer.chatwork.com/reference
"""
from __future__ import annotations

import time
from typing import Any

import requests

from .logger import setup_logger


logger = setup_logger(__name__)

BASE_URL = "https://api.chatwork.com/v2"
DEFAULT_TIMEOUT = 30
MAX_RETRY = 3


class ChatworkClient:
    """Chatwork API クライアント。

    使用するエンドポイントは2つだけ:
    - GET /my/tasks       : 自分担当の全タスク（全ルーム横断）
    - GET /rooms/{room_id}/messages/{message_id} : タスク元メッセージの投稿日時取得
    """

    def __init__(self, api_token: str) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-ChatWorkToken": api_token,
                "Accept": "application/json",
            }
        )

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """指数バックオフ付きGET。429/5xxはリトライ、4xxはそのまま例外。"""
        url = f"{BASE_URL}{path}"
        last_exc: Exception | None = None

        for attempt in range(1, MAX_RETRY + 1):
            try:
                response = self._session.get(
                    url, params=params, timeout=DEFAULT_TIMEOUT
                )
            except requests.RequestException as exc:
                last_exc = exc
                wait = 2 ** attempt
                logger.warning(
                    "Chatwork API リクエスト失敗 (%s) リトライ %d/%d in %ds: %s",
                    path,
                    attempt,
                    MAX_RETRY,
                    wait,
                    exc,
                )
                time.sleep(wait)
                continue

            if response.status_code == 429 or response.status_code >= 500:
                # レート制限 or サーバエラー → バックオフ
                wait = 2 ** attempt
                logger.warning(
                    "Chatwork API %d (%s) リトライ %d/%d in %ds",
                    response.status_code,
                    path,
                    attempt,
                    MAX_RETRY,
                    wait,
                )
                time.sleep(wait)
                last_exc = requests.HTTPError(
                    f"{response.status_code}: {response.text}"
                )
                continue

            response.raise_for_status()
            return response.json()

        # 全リトライ失敗
        raise RuntimeError(
            f"Chatwork API リトライ上限到達: {path}"
        ) from last_exc

    def list_my_tasks(self, status: str = "open") -> list[dict[str, Any]]:
        """自分担当のタスク一覧を返す。

        Returns:
            タスクdictのリスト。各dictの主要キー:
              task_id (int)
              room (dict: room_id, name, icon_path)
              assigned_by_account (dict: account_id, name, avatar_image_url)
              message_id (str)
              body (str)
              limit_time (int, Unix秒, 0なら未設定)
              limit_type (str: "none" | "date" | "time")
              status (str: "open" | "done")
        """
        return self._request("/my/tasks", params={"status": status})

    def get_message(self, room_id: int, message_id: str) -> dict[str, Any]:
        """メッセージ詳細を返す。`send_time` (Unix秒) を含む。"""
        return self._request(f"/rooms/{room_id}/messages/{message_id}")
