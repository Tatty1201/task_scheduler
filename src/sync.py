"""同期ロジック本体 (insert-only / 複数アカウント対応)。"""
from __future__ import annotations

from dataclasses import dataclass, field

from .chatwork_client import ChatworkClient
from .config import AppConfig, ChatworkAccount
from .google_calendar import GoogleCalendarClient, make_task_key
from .logger import setup_logger
from .sync_state import SyncStateStore
from .task_mapper import build_event_payload, needs_send_time


logger = setup_logger(__name__)


@dataclass
class AccountSummary:
    account_name: str
    fetched: int = 0
    already_synced: int = 0
    found_existing_on_calendar: int = 0
    created: int = 0
    failed: int = 0


@dataclass
class SyncSummary:
    accounts: list[AccountSummary] = field(default_factory=list)

    @property
    def total_created(self) -> int:
        return sum(a.created for a in self.accounts)

    @property
    def total_failed(self) -> int:
        return sum(a.failed for a in self.accounts)


def _sync_account(
    account: ChatworkAccount,
    config: AppConfig,
    gcal: GoogleCalendarClient,
    store: SyncStateStore,
    dry_run: bool,
) -> AccountSummary:
    """1アカウント分の同期を実行する。"""
    summary = AccountSummary(account_name=account.name)
    chatwork = ChatworkClient(account.api_token)

    try:
        tasks = chatwork.list_my_tasks(status="open")
    except Exception as exc:
        logger.error(
            "[%s] /my/tasks 取得失敗: %s", account.name, exc
        )
        summary.failed = -1  # アカウント単位の取得失敗
        return summary

    summary.fetched = len(tasks)
    logger.info("[%s] %d 件のオープンタスクを取得", account.name, summary.fetched)

    for task in tasks:
        task_id = int(task["task_id"])
        room = task.get("room") or {}
        room_id = int(room.get("room_id", 0))

        if store.is_synced(account.name, task_id):
            summary.already_synced += 1
            logger.debug(
                "[%s] スキップ (DB登録済み): task_id=%s", account.name, task_id
            )
            continue

        # DB保険: extendedProperties で既存検索
        task_key = make_task_key(account.name, task_id)
        existing_event_id = gcal.find_event_by_task_key(task_key)
        if existing_event_id:
            summary.found_existing_on_calendar += 1
            logger.info(
                "[%s] 既存イベント検出 → DB復元: task_id=%s event_id=%s",
                account.name,
                task_id,
                existing_event_id,
            )
            if not dry_run:
                store.save(account.name, task_id, room_id, existing_event_id)
            continue

        try:
            send_time: int | None = None
            if needs_send_time(task):
                message_id = task.get("message_id")
                if message_id and room_id:
                    try:
                        msg = chatwork.get_message(room_id, str(message_id))
                        send_time = int(msg.get("send_time", 0)) or None
                    except Exception as exc:
                        logger.warning(
                            "[%s] send_time 取得失敗 (task_id=%s): %s — 登録不可",
                            account.name,
                            task_id,
                            exc,
                        )
                        summary.failed += 1
                        continue

            payload = build_event_payload(
                task=task,
                account_name=account.name,
                send_time=send_time,
                timezone_name=config.timezone,
                default_start_time=config.default_start_time,
                duration_min=config.default_duration_min,
            )

            if dry_run:
                logger.info(
                    "[%s][dry-run] insert: task_id=%s title=%s start=%s",
                    account.name,
                    task_id,
                    payload["summary"],
                    payload["start"]["dateTime"],
                )
                summary.created += 1
                continue

            event_id = gcal.create_event(payload)
            store.save(account.name, task_id, room_id, event_id)
            summary.created += 1

        except Exception as exc:
            logger.error(
                "[%s] 同期失敗: task_id=%s err=%s", account.name, task_id, exc
            )
            summary.failed += 1

    logger.info(
        "[%s] 完了: 取得=%d 新規=%d スキップ(DB)=%d 既存検出=%d 失敗=%d",
        account.name,
        summary.fetched,
        summary.created,
        summary.already_synced,
        summary.found_existing_on_calendar,
        max(summary.failed, 0),
    )
    return summary


def run_sync(
    config: AppConfig,
    gcal: GoogleCalendarClient,
    store: SyncStateStore,
    dry_run: bool = False,
) -> SyncSummary:
    """全アカウントを順に同期する。"""
    overall = SyncSummary()

    for account in config.accounts:
        account_summary = _sync_account(
            account=account,
            config=config,
            gcal=gcal,
            store=store,
            dry_run=dry_run,
        )
        overall.accounts.append(account_summary)

    logger.info(
        "全アカウント完了: 新規登録合計=%d 失敗合計=%d",
        overall.total_created,
        overall.total_failed,
    )
    return overall
