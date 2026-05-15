# task_scheduler

Chatwork で「自分が担当」になっているタスクを、定期的に Google カレンダー（メインカレンダー）へ自動登録する Python CLI ツール。**複数の Chatwork アカウント**を1つのカレンダーに集約できる。

## 📚 ドキュメント

| 用途 | ファイル |
|---|---|
| はじめて使う方向けの丁寧な手順書 | **[USER_GUIDE.md](USER_GUIDE.md)** |
| 別PC・別ユーザーへの配布手順 | **[DISTRIBUTION.md](DISTRIBUTION.md)** |
| 開発者向けの設計メモ | [DESIGN.md](DESIGN.md) |
| この README | 開発者向けセットアップ・仕様 |

## 特徴

- **複数アカウント対応**: `accounts.yml` に複数のChatworkアカウントを登録でき、全アカウントのタスクを1つのカレンダーに集約する。
- **insert-only**: 一度カレンダーに登録したタスクは以後一切更新しないため、ユーザーがカレンダー上でドラッグして時刻や色を変えても上書きされない。
- **二重登録防止**: SQLite で `(account_name, task_id) → event_id` を管理 + `extendedProperties` でも検索することで、DB をリセットしても重複しない。
- **全ルーム横断**: `GET /my/tasks` 1 回で全ルームの自分担当タスクを取得（自分が依頼したタスクは対象外）。
- **期限なしタスクも取りこぼさない**: 登録日（メッセージ投稿日）の 10:00〜11:00 に登録する。

## 要件

- Python 3.10+
- Chatwork API トークン（アカウントごとに1つ）
- Google Cloud で作成した OAuth クライアント（Desktop App）

## セットアップ

### 1. 仮想環境と依存関係

```powershell
cd task_scheduler
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数（共通設定）

`.env.example` を `.env` にコピーして編集する。Chatwork系の認証情報は `.env` ではなく `accounts.yml` に記述する。

| キー | 説明 |
|------|------|
| `GOOGLE_CALENDAR_ID` | 既定 `primary`（メインカレンダー） |
| `TIMEZONE` | 既定 `Asia/Tokyo` |
| `DEFAULT_START_TIME` | 期限時刻なしの場合の開始時刻（既定 `10:00`） |
| `DEFAULT_DURATION_MIN` | 予定の長さ・分（既定 `60`） |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR`（既定 `INFO`） |

### 3. Chatwork アカウント設定

`accounts.yml.example` を `accounts.yml` にコピーして編集する。

```yaml
accounts:
  - name: main                       # 内部識別子 (重複防止に使用、カレンダー表示には出ない)
    chatwork_api_token: xxxxxxxx...
    chatwork_my_account_id: 1234567

  - name: client_a
    chatwork_api_token: yyyyyyyy...
    chatwork_my_account_id: 7654321
```

- `name` は **半角英数 / `_` / `-` の1〜32文字、ユニーク**にすること（例: `main`, `client_a`, `personal`）
- カレンダーには表示されない内部識別子
- Chatwork API トークン: [Chatwork の管理画面](https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php) で発行
- `chatwork_my_account_id`: Chatwork プロフィールURLの末尾の数字

### 4. Google OAuth クライアントの用意

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. 「APIとサービス」→「ライブラリ」で **Google Calendar API** を有効化
3. 「APIとサービス」→「OAuth 同意画面」を構成（テスト ユーザーに自分のアカウントを追加）
4. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」→ アプリケーションの種類 **デスクトップアプリ**
5. 作成された JSON を `credentials.json` としてこのフォルダ直下に配置

### 5. 初回認証

```powershell
python main.py auth
```

ブラウザが開くので Google アカウントで認可する。完了すると `token.json` が生成される。

### 6. 動作確認（カレンダーに書き込まないドライラン）

```powershell
python main.py sync --dry-run
```

問題なければ実書き込み:

```powershell
python main.py sync
```

## Windows タスクスケジューラへの登録（1日8回 / 3時間おき）

1. **タスクの作成**を開く
2. 「全般」タブ
   - 名前: `Chatwork → Google Calendar 同期`
   - 「ユーザーがログオンしているかどうかにかかわらず実行する」を選択
3. 「トリガー」タブ → 新規
   - 開始: 任意の日付の `00:00:00`
   - 繰り返し間隔: **3時間** / 継続時間: **無期限**
4. 「操作」タブ → 新規
   - プログラム/スクリプト: `<task_scheduler>\.venv\Scripts\python.exe`
   - 引数の追加: `main.py sync`
   - 開始（オプション）: `<task_scheduler>` の絶対パス
5. 「条件」「設定」は要件に合わせて調整

これで 00:00 / 03:00 / 06:00 / 09:00 / 12:00 / 15:00 / 18:00 / 21:00 に同期が走る。

## コマンド一覧

| コマンド | 動作 |
|---------|------|
| `python main.py auth` | Google OAuth ブラウザ認可（初回 / 再認証） |
| `python main.py sync` | `accounts.yml` の全アカウントを順に同期 |
| `python main.py sync --dry-run` | カレンダーに書き込まずログ出力 |
| `python main.py reset` | `sync_state.db` を初期化（カレンダーのイベントは残る） |

## 動作仕様

### 取得対象

- 各アカウントごとに `GET /my/tasks?status=open` で取得
- `status=done`（完了）は対象外
- 自分が依頼したタスクは対象外

### 日時マッピング

| `limit_type` | カレンダーに入る時間 |
|---|---|
| `time` | 期限時刻 〜 +1時間（例 14:30 → 14:30〜15:30） |
| `date` | 期限当日の 10:00〜11:00 |
| `none` | 登録日（メッセージ投稿日）の 10:00〜11:00 |

開始時刻 `10:00` と長さ `60` 分は `.env` で変更可能。

### イベント内容

- タイトル: `[ルーム名] タスク本文の先頭80文字` （アカウント名は含めない）
- 説明:
  ```
  依頼者: <Chatworkの依頼者名>
  登録日時: YYYY-MM-DD HH:MM
  Chatworkで開く: https://www.chatwork.com/#!rid{room_id}-{message_id}
  task_id: <Chatwork task_id>
  ```
- 隠しメタデータ: `extendedProperties.private.chatwork_task_key = <account_name>:<task_id>`（重複検出用）

### 重複防止の仕組み

複数アカウントで同じ `task_id` が振られる可能性があるため、内部キーは `(account_name, task_id)` の複合キー。

1. SQLite `task_events` に `(account_name, task_id) → event_id` を保存
2. 新規登録時は `events.list(privateExtendedProperty=chatwork_task_key=<account>:<id>)` で念のため検索 → 見つかれば DB に書き戻してスキップ

## トラブルシュート

- **`credentials.json が見つかりません`**: セットアップ 4 を実施。
- **`accounts.yml が見つかりません`**: `accounts.yml.example` を `accounts.yml` にコピー。
- **トークン期限切れ**: `python main.py auth` で再認証。
- **特定アカウントだけ取得失敗**: ログに `[<account_name>] /my/tasks 取得失敗` が出る。API トークンの有効性を確認。他のアカウントは影響を受けず継続。
- **タスクが取れない**: Chatwork API のトークン権限と `status=open` を確認。
- **`No time zone found with key Asia/Tokyo`（Windows）**: IANA タイムゾーンデータが無いと出る。`pip install -r requirements.txt` で `tzdata` を入れる（`requirements.txt` に含めてある）。

## よくある質問

### iPhone / Mac の Apple カレンダーアプリで見れますか？

iPhone・Mac の **設定で Google アカウントを追加** すれば、Apple カレンダーアプリにも Google カレンダーの予定が同期されて表示されます。このツール側の変更は不要です。

- **iPhone**: 設定 → カレンダー → アカウント → アカウントを追加 → Google
- **Mac**: システム設定 → インターネットアカウント → Google

iCloud カレンダーに **直接** 書き込みたい場合は別途 CalDAV 対応の実装が必要です（現在は未対応）。

## 関連ドキュメント

- 設計詳細: [DESIGN.md](DESIGN.md)
- 利用マニュアル（非開発者向け）: [USER_GUIDE.md](USER_GUIDE.md)
- 配布ガイド: [DISTRIBUTION.md](DISTRIBUTION.md)
- 開発ルール: `../_core/principles/dev-rules-python.md`
