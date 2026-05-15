"""Google Calendar API クライアント (OAuth Desktop App フロー)。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .logger import setup_logger


logger = setup_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# extendedProperties.private に入れる重複検出用キー
# value は f"{account_name}:{task_id}" の形式
TASK_KEY_PROPERTY = "chatwork_task_key"


def authenticate(credentials_path: Path, token_path: Path) -> Credentials:
    """対話型 OAuth フロー。ブラウザを開いてユーザー認可を得る。

    既に有効な token.json があれば使い、期限切れなら refresh、
    refresh も無理なら再認可する。
    """
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        logger.info("Google認証トークンを refresh します")
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"{credentials_path} が見つかりません。"
            " GCPコンソールで OAuth Desktop App のクライアントIDを作成し、"
            " JSON を credentials.json として配置してください。"
        )

    logger.info("Google OAuth ブラウザ認証を開始します")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), SCOPES
    )
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    logger.info("認証トークンを %s に保存しました", token_path)
    return creds


def make_task_key(account_name: str, task_id: int) -> str:
    """重複検出に使う task_key を組み立てる。"""
    return f"{account_name}:{task_id}"


class GoogleCalendarClient:
    """Google Calendar API ラッパー。"""

    def __init__(self, credentials: Credentials, calendar_id: str) -> None:
        self._service = build(
            "calendar", "v3", credentials=credentials, cache_discovery=False
        )
        self._calendar_id = calendar_id

    def find_event_by_task_key(self, task_key: str) -> str | None:
        """extendedProperties で検索し、既存イベントのIDを返す。"""
        try:
            response = (
                self._service.events()
                .list(
                    calendarId=self._calendar_id,
                    privateExtendedProperty=f"{TASK_KEY_PROPERTY}={task_key}",
                    maxResults=1,
                    showDeleted=False,
                )
                .execute()
            )
        except HttpError as exc:
            logger.error("既存イベント検索エラー (key=%s): %s", task_key, exc)
            return None

        items = response.get("items", [])
        if not items:
            return None
        return items[0].get("id")

    def create_event(self, payload: dict[str, Any]) -> str:
        """イベントを新規作成し、event_id を返す。"""
        event = (
            self._service.events()
            .insert(calendarId=self._calendar_id, body=payload)
            .execute()
        )
        event_id = event["id"]
        logger.info(
            "カレンダー登録: event_id=%s title=%s",
            event_id,
            payload.get("summary"),
        )
        return event_id
