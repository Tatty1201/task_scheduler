"""Chatwork → Googleカレンダー 同期ツール エントリポイント。

使い方:
    python main.py auth                # 初回認証 (ブラウザを開く)
    python main.py sync                # 1回同期する (accounts.yml の全アカウント)
    python main.py sync --dry-run      # 書き込まずログ出力のみ
    python main.py reset               # sync_state.db を初期化
"""
from __future__ import annotations

import argparse
import sys

from src.config import load_config
from src.google_calendar import GoogleCalendarClient, authenticate
from src.logger import setup_logger
from src.sync import run_sync
from src.sync_state import SyncStateStore


logger = setup_logger("task_scheduler")


def cmd_auth() -> int:
    """Google OAuth 認可フローのみ実行する。"""
    config = load_config()
    authenticate(config.credentials_path, config.token_path)
    logger.info("認証完了: %s", config.token_path)
    return 0


def cmd_sync(dry_run: bool) -> int:
    """同期コマンド。"""
    config = load_config()
    logger.info(
        "同期開始: アカウント数=%d 対象カレンダー=%s dry_run=%s",
        len(config.accounts),
        config.google_calendar_id,
        dry_run,
    )

    creds = authenticate(config.credentials_path, config.token_path)
    gcal = GoogleCalendarClient(creds, config.google_calendar_id)

    with SyncStateStore(config.db_path) as store:
        summary = run_sync(config, gcal, store, dry_run=dry_run)

    # アカウント取得失敗 (failed=-1) または個別失敗があれば 1
    has_failure = any(
        (a.failed == -1) or (a.failed > 0) for a in summary.accounts
    )
    return 1 if has_failure else 0


def cmd_reset() -> int:
    """同期状態DBをクリアする (カレンダーのイベントは消さない)。"""
    config = load_config()
    with SyncStateStore(config.db_path) as store:
        store.reset()
    logger.info("sync_state.db を初期化しました")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task_scheduler",
        description="Chatwork タスクを Google カレンダーに自動登録する",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("auth", help="Google OAuth 認可")

    p_sync = subparsers.add_parser("sync", help="1回同期する")
    p_sync.add_argument(
        "--dry-run",
        action="store_true",
        help="カレンダーに書き込まずログ出力のみ",
    )

    subparsers.add_parser("reset", help="sync_state.db を初期化")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "auth":
            return cmd_auth()
        if args.command == "sync":
            return cmd_sync(dry_run=args.dry_run)
        if args.command == "reset":
            return cmd_reset()
    except Exception as exc:
        logger.exception("実行中に例外が発生: %s", exc)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
