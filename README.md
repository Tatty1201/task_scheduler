# task_scheduler — Chatwork Tasks → Google Calendar

[![CI](https://github.com/Tatty1201/task_scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/Tatty1201/task_scheduler/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Chatworkで自分に割り当てられたタスクを、Google Calendarへ自動登録するローカル実行型のPython CLIです。**
複数のChatworkアカウントを1つのGoogle Calendarへ集約できます。

> A small, local-first Python CLI that syncs your assigned Chatwork tasks into Google Calendar. It supports multiple Chatwork accounts and keeps user credentials on the machine running the tool.

## Project status

**Early public OSS / testers welcome.**

現在は実運用で使いながら、第三者が安全に導入できる形へ整備しています。バグ報告、導入時につまずいた点、ドキュメント改善、Pull Requestを歓迎します。

- GitHub Issues: バグ・改善要望
- Pull Requests: 小さく焦点を絞った改善を歓迎
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security: [SECURITY.md](SECURITY.md)
- Changes / releases: [CHANGELOG.md](CHANGELOG.md)

## Why this exists

Chatworkのタスクを仕事の入口として使っていても、実際の一日の時間管理はGoogle Calendarで行う人は少なくありません。
このツールは、その間の「タスクを予定に写す」作業を自動化します。

設計上のポイントは **insert-only** です。
一度Google Calendarへ登録したイベントは、その後このツールから更新しません。カレンダー上で時間・色・タイトルなどを手で変えても、次回同期で上書きされません。

## Features

- **複数Chatworkアカウント対応** — 複数アカウントの自分担当タスクを1つのカレンダーへ集約
- **Insert-only** — 登録後のカレンダー編集を尊重し、自動で上書きしない
- **二重登録防止** — SQLite + Google Calendar `extendedProperties` の二段構え
- **全ルーム横断** — Chatwork `GET /my/tasks` で自分担当の未完了タスクを取得
- **期限なしタスク対応** — 元メッセージ投稿日を基準に予定化
- **Dry run** — 書き込み前に取得内容を確認可能
- **ローカル認証情報** — APIトークン/OAuthトークンをGitに入れず、実行PCに保持
- **自動テスト** — GitHub Actionsで複数Pythonバージョンを検証

## Requirements

- Python 3.10+
- Chatwork API token（アカウントごと）
- Google Cloudで作成したOAuth client（Desktop App）

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/Tatty1201/task_scheduler.git
cd task_scheduler
python -m venv .venv
```

仮想環境を有効化します。

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

依存関係をインストールします。

```bash
pip install -r requirements.txt
```

### 2. Create local config

```bash
cp .env.example .env
cp accounts.yml.example accounts.yml
```

Windowsではエクスプローラー等でコピーしても構いません。

`accounts.yml` にChatworkアカウントを設定します。

```yaml
accounts:
  - name: main
    chatwork_api_token: your_token_here
    chatwork_my_account_id: 1234567
```

複数アカウントを使う場合は項目を追加します。

```yaml
accounts:
  - name: main
    chatwork_api_token: token_for_main
    chatwork_my_account_id: 1234567

  - name: client_a
    chatwork_api_token: token_for_client_a
    chatwork_my_account_id: 7654321
```

`name` は内部識別用です。半角英数字・`_`・`-` の1〜32文字で、アカウントごとに重複しない値を設定してください。

### 3. Set up Google Calendar OAuth

初回はセットアップウィザードを実行します。

```bash
python main.py setup-google
```

ウィザードはGoogle Cloud Consoleの必要ページを案内し、`credentials.json` の確認からOAuth認証まで進めます。

手動で行う場合は以下です。

1. Google Cloudでプロジェクトを作成
2. Google Calendar APIを有効化
3. OAuth同意画面を構成
4. OAuth Client ID（Desktop App）を作成
5. ダウンロードしたJSONを `credentials.json` としてプロジェクト直下へ置く
6. `python main.py auth` を実行

### 4. Dry run

最初はカレンダーへ書き込まず確認します。

```bash
python main.py sync --dry-run
```

### 5. Sync

```bash
python main.py sync
```

## Commands

| Command | Description |
|---|---|
| `python main.py setup-google` | Google Calendar OAuthの初回セットアップを案内 |
| `python main.py setup-google --no-browser` | URLを表示するだけでブラウザを自動起動しない |
| `python main.py setup-google --skip-auth` | `credentials.json` の検証まで実行 |
| `python main.py auth` | Google OAuth認証のみ実行 |
| `python main.py sync --dry-run` | カレンダーへ書かず同期内容を確認 |
| `python main.py sync` | 全アカウントを同期 |
| `python main.py reset` | ローカル同期状態DBを初期化（Google Calendarのイベントは残る） |

## How task dates are mapped

| Chatwork `limit_type` | Google Calendar |
|---|---|
| `time` | 指定された期限時刻から `DEFAULT_DURATION_MIN` 分 |
| `date` | 期限日の `DEFAULT_START_TIME` から開始 |
| `none` | 元メッセージ投稿日の `DEFAULT_START_TIME` から開始 |

既定値は `.env` で変更できます。

```dotenv
GOOGLE_CALENDAR_ID=primary
TIMEZONE=Asia/Tokyo
DEFAULT_START_TIME=10:00
DEFAULT_DURATION_MIN=60
LOG_LEVEL=INFO
```

## Duplicate prevention

同じタスクを何度もカレンダーへ作らないため、2段階で確認します。

1. SQLite `sync_state.db` に `(account_name, task_id) -> event_id` を保存
2. Google Calendar側にも `extendedProperties.private.chatwork_task_key` を保存して検索

そのためローカルDBを失っても、Calendar側のメタデータが残っていれば重複を検出できます。

## Automatic execution

このCLIをOSのスケジューラから定期実行できます。

Windowsでは「タスク スケジューラ」から、たとえば3時間おきに以下を実行します。

```text
<project>\.venv\Scripts\python.exe main.py sync
```

詳しい配布・定期実行手順は [DISTRIBUTION.md](DISTRIBUTION.md) を参照してください。

## Privacy and credentials

このプロジェクト自身が運営するサーバーはありません。認証情報は実行するPCに保存します。

Gitにコミットしてはいけないファイル:

- `.env`
- `accounts.yml`
- `credentials.json`
- `token.json`
- `sync_state.db`

これらは `.gitignore` で除外されています。

誤って認証情報をGitへコミットした場合は、後からファイルを削除するだけではなく、該当トークンや認証情報を必ず失効・再発行してください。

## Current limitations

- **Insert-only:** Chatwork側でタスク本文や期限を後から変更しても、既に作成済みのCalendarイベントには反映しません。
- **Chatwork API limit:** `GET /my/tasks` は1回の取得で最大100件です。100件を超える未完了タスクを常時持つ運用では取りこぼす可能性があります。
- **Google OAuth setup:** 現在は各利用者が自分のGoogle Cloudプロジェクト/OAuth Clientを用意する方式です。
- **Calendar target:** 現在は全Chatworkアカウントを共通の `GOOGLE_CALENDAR_ID` に集約します。

## Development

開発用依存関係を追加します。

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

テスト:

```bash
python -m pytest -q
```

Pull RequestではGitHub ActionsのCIも自動実行されます。

## Roadmap

- [ ] 第三者によるセットアップ検証と導入手順改善
- [ ] 初回 `v0.1.0` リリース
- [ ] アカウントごとのCalendar ID
- [ ] より分かりやすい初回セットアップ
- [ ] エラー表示・設定バリデーション改善
- [ ] macOS / Linuxの定期実行ガイド強化
- [ ] 実利用者からのIssueをもとに優先順位を更新

## Documentation

| Document | Purpose |
|---|---|
| [USER_GUIDE.md](USER_GUIDE.md) | 初めて使う方向けの詳しい手順 |
| [DISTRIBUTION.md](DISTRIBUTION.md) | 別PC・別ユーザーへの配布と定期実行 |
| [DESIGN.md](DESIGN.md) | アーキテクチャと設計判断 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 開発参加方法 |
| [SECURITY.md](SECURITY.md) | セキュリティ報告方針 |
| [CHANGELOG.md](CHANGELOG.md) | 変更履歴とRelease準備 |

## Contributing

バグ報告・改善案・Pull Requestを歓迎します。
まず [CONTRIBUTING.md](CONTRIBUTING.md) を確認してください。

特に、**実際にセットアップして詰まった場所をIssueで教えてもらうこと**は大きな助けになります。

## License

MIT License. See [LICENSE](LICENSE).
