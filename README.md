# task_scheduler — Chatwork Tasks → Google Calendar

[![CI](https://github.com/Tatty1201/task_scheduler/actions/workflows/ci.yml/badge.svg)](https://github.com/Tatty1201/task_scheduler/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Chatworkで自分に割り当てられたタスクを、Google Calendarへ自動登録するローカル実行型のPython CLIです。**
複数のChatworkアカウントを1つのGoogle Calendarへ集約できます。

> A local-first Python CLI that syncs assigned Chatwork tasks into Google Calendar while keeping credentials on your own machine.

## Project status

**Early public OSS / testers welcome.**

現在は実運用しながら、第三者が迷わず導入できる形へ改善しています。バグ報告、セットアップで詰まった点、ドキュメント改善、Pull Requestを歓迎します。

- 初めて使う人: [USER_GUIDE.md](USER_GUIDE.md)
- 開発に参加する人: [CONTRIBUTING.md](CONTRIBUTING.md)
- セキュリティ: [SECURITY.md](SECURITY.md)
- 変更履歴: [CHANGELOG.md](CHANGELOG.md)

## Why this exists

Chatworkでタスクを受け取っても、一日の時間管理はGoogle Calendarで行っている人向けです。
「Chatworkのタスクをカレンダーへ写す」作業だけを自動化します。

設計上の特徴は **insert-only** です。一度Google Calendarへ登録したイベントを、このツールは後から上書きしません。カレンダー上で時間・色・タイトルを手で変えても、その編集を尊重します。

## Features

- **複数Chatworkアカウント対応** — 複数アカウントの自分担当タスクを1つのカレンダーへ集約
- **Insert-only** — 登録後のカレンダー編集を上書きしない
- **二重登録防止** — SQLite + Google Calendar `extendedProperties` の二段構え
- **全ルーム横断** — Chatwork `GET /my/tasks` で未完了の自分担当タスクを取得
- **期限なしタスク対応** — 元メッセージ投稿日を基準に予定化
- **Dry run** — 書き込み前に同期内容を確認可能
- **Local-first credentials** — APIトークン/OAuthトークンは実行PCに保持
- **Automated tests** — GitHub Actionsで複数Pythonバージョンを検証

## Requirements

- Python 3.10+
- Chatwork API token（アカウントごとに1つ）
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

`.env.example` と `accounts.yml.example` をコピーします。

**macOS / Linux**

```bash
cp .env.example .env
cp accounts.yml.example accounts.yml
```

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
Copy-Item accounts.yml.example accounts.yml
```

`accounts.yml` にChatwork APIトークンを設定します。

```yaml
accounts:
  - name: main
    chatwork_api_token: your_token_here
```

複数アカウントを使う場合は追加します。

```yaml
accounts:
  - name: main
    chatwork_api_token: token_for_main

  - name: client_a
    chatwork_api_token: token_for_client_a
```

`name` は重複防止に使う内部識別子です。半角英数字・`_`・`-` の1〜32文字で、アカウントごとに一意にしてください。カレンダーには表示されません。

> 以前のバージョンで使っていた `chatwork_my_account_id` が `accounts.yml` に残っていても問題ありません。現在の同期処理では不要で、無視されます。

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

Google CalendarにChatworkタスクが追加されれば成功です。

## Commands

| Command | Description |
|---|---|
| `python main.py setup-google` | Google Calendar OAuthの初回セットアップを案内 |
| `python main.py setup-google --no-browser` | URLだけ表示しブラウザを自動起動しない |
| `python main.py setup-google --skip-auth` | `credentials.json` の検証まで実行 |
| `python main.py auth` | Google OAuth認証のみ実行 |
| `python main.py sync --dry-run` | カレンダーへ書かず同期内容を確認 |
| `python main.py sync` | 全アカウントを同期 |
| `python main.py reset` | ローカル同期状態DBを初期化（Calendarイベントは残す） |

## Date mapping

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

同じタスクを何度も作らないため、2段階で確認します。

1. SQLite `sync_state.db` に `(account_name, task_id) -> event_id` を保存
2. Google Calendar側にも `extendedProperties.private.chatwork_task_key` を保存して検索

ローカルDBを失っても、Calendar側のメタデータが残っていれば重複を検出できます。

## Automatic execution

OSのスケジューラから定期実行できます。

Windowsでは「タスク スケジューラ」から、たとえば3時間おきに以下を実行します。

```text
<project>\.venv\Scripts\python.exe main.py sync
```

詳しくは [DISTRIBUTION.md](DISTRIBUTION.md) を参照してください。

## Privacy and credentials

このプロジェクト自身が運営するサーバーはありません。認証情報は実行するPCに保存します。

Gitへコミットしてはいけないファイル:

- `.env`
- `accounts.yml`
- `credentials.json`
- `token.json`
- `sync_state.db`

これらは `.gitignore` で除外されています。

誤って認証情報をGitへコミットした場合は、後から削除するだけでなく、該当トークンや認証情報を必ず失効・再発行してください。

## Current limitations

- **Insert-only:** Chatwork側で本文や期限を後から変更しても、作成済みCalendarイベントには反映しません。
- **Chatwork API limit:** `GET /my/tasks` は1回の取得で最大100件です。100件を超える未完了タスクを常時持つ運用では取りこぼす可能性があります。
- **Google OAuth setup:** 現在は各利用者が自分のGoogle Cloudプロジェクト/OAuth Clientを用意する方式です。
- **Calendar target:** 現在は全Chatworkアカウントを共通の `GOOGLE_CALENDAR_ID` に集約します。

## Development

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

Pull RequestではGitHub ActionsのCIも自動実行されます。

## Roadmap

- [ ] 第三者によるfresh install検証と導入手順改善
- [ ] 初回 `v0.1.0` リリース
- [ ] アカウントごとのCalendar ID
- [ ] 初回セットアップのさらなる簡略化
- [ ] エラー表示・設定バリデーション改善
- [ ] macOS / Linuxの定期実行ガイド強化
- [ ] 実利用者からのIssueをもとに優先順位を更新

## Documentation

| Document | Purpose |
|---|---|
| [USER_GUIDE.md](USER_GUIDE.md) | 初めて使う方向けの詳しい手順 |
| [DISTRIBUTION.md](DISTRIBUTION.md) | 別PC・別ユーザーへの導入と定期実行 |
| [DESIGN.md](DESIGN.md) | アーキテクチャと設計判断 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 開発参加方法 |
| [SECURITY.md](SECURITY.md) | セキュリティ報告方針 |
| [CHANGELOG.md](CHANGELOG.md) | 変更履歴とRelease準備 |

## Contributing

バグ報告・改善案・Pull Requestを歓迎します。まず [CONTRIBUTING.md](CONTRIBUTING.md) を確認してください。

特に、**実際にセットアップして詰まった場所をIssueで教えてもらうこと**が大きな助けになります。

## License

MIT License. See [LICENSE](LICENSE).
