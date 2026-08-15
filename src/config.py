"""アプリ設定を `.env` と `accounts.yml` から読み込むモジュール。"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
ENV_PATH: Path = PROJECT_ROOT / ".env"
ACCOUNTS_PATH: Path = PROJECT_ROOT / "accounts.yml"

# 副作用: import 時に .env を読み込む
load_dotenv(ENV_PATH)


# name に使える文字: 半角英数 + アンダースコア + ハイフン (1〜32文字)
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


@dataclass(frozen=True)
class ChatworkAccount:
    """1つのChatworkアカウントの認証情報。"""

    name: str  # 内部識別子 (重複防止キーに使う)
    api_token: str


@dataclass(frozen=True)
class AppConfig:
    """アプリ全体の設定値。"""

    accounts: list[ChatworkAccount]
    google_calendar_id: str
    timezone: str
    default_start_time: str
    default_duration_min: int

    # ファイルパス
    credentials_path: Path
    token_path: Path
    db_path: Path


def _load_accounts(path: Path) -> list[ChatworkAccount]:
    """accounts.yml から Chatwork アカウント一覧を読み込む。

    `chatwork_my_account_id` は過去の設定との後方互換のためファイル内に
    残っていてもよいが、同期処理には不要なので読み込まない。
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} が見つかりません。"
            " accounts.yml.example を accounts.yml にコピーして編集してください。"
        )

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    items = raw.get("accounts")
    if not isinstance(items, list) or not items:
        raise ValueError(
            f"{path} の 'accounts' リストが空です。最低1件登録してください。"
        )

    accounts: list[ChatworkAccount] = []
    seen_names: set[str] = set()
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{path} の accounts[{idx}] が dict ではありません")

        name = str(item.get("name", "")).strip()
        token = str(item.get("chatwork_api_token", "")).strip()

        if not name:
            raise ValueError(f"{path} accounts[{idx}].name が空です")
        if not NAME_PATTERN.match(name):
            raise ValueError(
                f"{path} accounts[{idx}].name='{name}' は不正です"
                " (半角英数/アンダースコア/ハイフンのみ、1〜32文字)"
            )
        if name in seen_names:
            raise ValueError(f"{path} accounts[].name='{name}' が重複しています")
        if not token:
            raise ValueError(f"{path} accounts[{idx}].chatwork_api_token が空です")

        accounts.append(ChatworkAccount(name=name, api_token=token))
        seen_names.add(name)

    return accounts


def load_config() -> AppConfig:
    """環境変数 + accounts.yml から設定を組み立てる。"""
    accounts = _load_accounts(ACCOUNTS_PATH)

    return AppConfig(
        accounts=accounts,
        google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        timezone=os.getenv("TIMEZONE", "Asia/Tokyo"),
        default_start_time=os.getenv("DEFAULT_START_TIME", "10:00"),
        default_duration_min=int(os.getenv("DEFAULT_DURATION_MIN", "60")),
        credentials_path=PROJECT_ROOT / "credentials.json",
        token_path=PROJECT_ROOT / "token.json",
        db_path=PROJECT_ROOT / "sync_state.db",
    )
