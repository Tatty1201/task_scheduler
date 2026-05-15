# DESIGN — task_scheduler

## ゴール

複数の Chatwork アカウントで自分が担当のタスクを Google カレンダーに自動登録する。登録後はユーザーがカレンダー上でドラッグして自由に編集できるよう、**insert-only**（一度登録したら触らない）方針を取る。

## アーキテクチャ

```
Windows タスクスケジューラ (3時間おき)
        │
        ▼
   main.py sync
        │
        ├─ accounts.yml ── 複数アカウントを読み込み
        │
        └─ アカウントごとに以下を順次実行
             ├─ Chatwork API ── GET /my/tasks?status=open
             │                  GET /rooms/{room_id}/messages/{message_id} (新規タスクのみ)
             ├─ SQLite (sync_state.db) ── (account_name, task_id) 既登録チェック
             └─ Google Calendar API ── events.list (privateExtendedProperty 検索)
                                       events.insert
```

## モジュール構成

| ファイル | 責務 |
|---|---|
| `main.py` | CLI エントリポイント（auth / sync / reset） |
| `src/config.py` | `.env` + `accounts.yml` 読み込み・設定値の保持 |
| `src/logger.py` | logging セットアップ |
| `src/chatwork_client.py` | Chatwork API 薄いラッパー（`list_my_tasks` / `get_message`） |
| `src/google_calendar.py` | OAuth + events.insert / events.list |
| `src/sync_state.py` | SQLite で `(account_name, task_id) ↔ event_id` を永続化 |
| `src/task_mapper.py` | Chatworkタスク → Google イベント payload 変換 |
| `src/sync.py` | 全アカウントを順に同期する insert-only ロジック |

## 主要な設計判断

### 1. insert-only

カレンダー上でユーザーが手編集したイベントを同期側が上書きしないため、一度登録した `(account_name, task_id)` は二度と更新しない。Chatwork 側で本文や期限が変わってもカレンダーには反映されない。

### 2. 複数アカウント対応

- `accounts.yml` に複数の Chatwork API トークンを記述
- 認証情報は git に上がらないように `.gitignore` で除外
- `name` フィールドは内部識別子のみ（カレンダーに表示しない）
- アカウント単位で `/my/tasks` が失敗しても他アカウントの同期は継続する
- すべてのアカウントのタスクを同じ Google カレンダー（既定 `primary`）に集約

### 3. 二段重複防止 + 複合キー

複数アカウントで同じ `task_id` が振られる可能性があるため、内部キーは `(account_name, task_id)` の複合キーとする。

| レベル | 内容 |
|---|---|
| L1 | SQLite に `(account_name, task_id)` があれば即スキップ（API コール 0） |
| L2 | `events.list(privateExtendedProperty=chatwork_task_key=<account>:<id>)` で念のため検索。見つかれば DB に復元してスキップ。 |

DB が破損／初期化されても L2 で重複登録は防げる。

### 4. 期限なしタスクの扱い

`limit_type=none` のタスクは「登録日（元メッセージの `send_time` の日付）の 10:00〜11:00」に登録する。`send_time` 取得には追加で 1 回 API を叩く必要があるが、新規タスク（DB未登録）に対してのみ呼ぶため呼び出し回数は最小。

### 5. レート制限への余裕

Chatwork API のレート制限は **アカウント単位で5分間に300リクエスト**。1回の sync でアカウントあたり叩くのは:

- `/my/tasks` × 1
- `/messages/{id}` × 新規タスク数

複数アカウントでも各アカウントの上限は独立しているため十分余裕がある。

## DB スキーマ

```sql
CREATE TABLE task_events (
    account_name TEXT    NOT NULL,
    task_id      INTEGER NOT NULL,
    room_id      INTEGER NOT NULL,
    event_id     TEXT    NOT NULL,
    synced_at    TEXT    NOT NULL,
    PRIMARY KEY (account_name, task_id)
);
```

## extendedProperties 設計

| キー | 値 | 用途 |
|---|---|---|
| `chatwork_task_key` | `<account_name>:<task_id>` | 重複検出（events.list で検索） |

## TODO / 将来の拡張

- [ ] 自分が依頼したタスクの追加同期オプション（`--mode=created_by_me`）
- [ ] アカウントごとにカレンダーを変える設定（`accounts.yml` に `calendar_id` を追加）
- [ ] 完了したタスクのイベントタイトルに `✅` を付ける（運用見直し時）
- [ ] サマリ通知（同期件数を Slack 等に投げる）
- [ ] 単体テスト（`task_mapper` の日時計算、`sync_state` の複合キー動作）
