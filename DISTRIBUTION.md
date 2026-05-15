# コード配布ガイド

このツールを別の人・別のPCで動かすための手順をまとめます。

---

## 大原則

**コードは共有してOK、個人情報・認証情報は絶対に共有しない**

| 共有してOK | 絶対に共有しない |
|---|---|
| `*.py` ファイル全部 | `.env` |
| `requirements.txt` | `accounts.yml`（API トークンが入っている） |
| `.gitignore` | `credentials.json`（Google OAuth クライアント） |
| `.env.example` | `token.json`（Google アクセストークン） |
| `accounts.yml.example` | `sync_state.db`（同期履歴） |
| `README.md` / `USER_GUIDE.md` / `DISTRIBUTION.md` / `DESIGN.md` | `.venv/`（仮想環境フォルダ） |

これらの「共有しない」ファイルは `.gitignore` で除外済みなので、Git で配布する場合は心配不要です。

---

## 配布方法

### 方法A: ZIP で渡す（一番簡単）

1. **`task_scheduler` フォルダを丸ごとコピー**して別の場所（例: デスクトップ）に置く
2. コピーしたフォルダの中から **以下を削除**:
   - `.venv/` フォルダ
   - `.env` ファイル
   - `accounts.yml` ファイル
   - `credentials.json` ファイル
   - `token.json` ファイル
   - `sync_state.db` ファイル
   - `__pycache__/` フォルダ（あれば）
3. 残ったフォルダを ZIP で圧縮して渡す

### 方法B: Git で渡す

`.gitignore` で除外設定済みなので、安全に共有できます。

```powershell
cd task_scheduler
git init
git add .
git commit -m "initial commit"
# GitHub などに push する
```

受け取る側:
```powershell
git clone <リポジトリURL>
cd task_scheduler
```

> 確認: ZIP 化やコミット前に必ず `.env` `accounts.yml` `credentials.json` `token.json` が含まれていないことをチェックしてください。

---

## 別PC・別アカウントでセットアップする手順

受け取った側のセットアップは、基本的に [USER_GUIDE.md](USER_GUIDE.md) のステップ1〜8をそのまま実行すれば動きます。

ここでは「**配布を受け取った人がすること**」を簡潔にまとめます。

### 必要なもの（受け取る人が自分で用意）

1. **Python 3.10 以上**（[インストール手順](USER_GUIDE.md#ステップ1-python-をインストール)）
2. **自分の Chatwork アカウント**（API トークン取得が可能であること）
3. **自分の Google アカウント**

### 配布を受け取った人の手順

#### 1. 配布されたフォルダを置く

ZIP なら解凍、Git なら clone。お好みの場所（例: `Documents\task_scheduler`）に置きます。

#### 2. 自分用の設定ファイルを作る

フォルダ内の例ファイルをコピーして自分用にする:

```powershell
cd "C:\Users\(あなたのユーザー名)\Documents\task_scheduler"
Copy-Item .env.example .env
Copy-Item accounts.yml.example accounts.yml
```

#### 3. Chatwork トークンとアカウントID を `accounts.yml` に書く

メモ帳で `accounts.yml` を開いて編集:

```yaml
accounts:
  - name: main
    chatwork_api_token: 自分のChatwork APIトークン
    chatwork_my_account_id: 自分のChatworkアカウントID（数字）
```

トークン取得は [USER_GUIDE のステップ3〜4](USER_GUIDE.md#ステップ3-chatwork-api-トークンを取得) を参照。

#### 4. 自分の Google Cloud プロジェクトを作って `credentials.json` を入手

Google の OAuth は **配布元の人とは別に、受け取った人自身が自分のGoogle Cloudプロジェクトを作る必要があります**。

理由:
- OAuth クライアントは「テストユーザー」を最大100名までしか登録できない
- セキュリティ上、配布元の `credentials.json` を共有するのは推奨されない
- 配布元の Google Cloud プロジェクトに依存すると、配布元がプロジェクトを消した瞬間に全員動かなくなる

手順は [USER_GUIDE のステップ5](USER_GUIDE.md#ステップ5-google-アカウントの設定一番ややこしい) を参照。
ダウンロードした `credentials.json` を `task_scheduler` フォルダ直下に置く。

#### 5. 仮想環境を作って依存ライブラリをインストール

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### 6. Google 認証

**おすすめ:** Console の必要ページを順に開き、`credentials.json` を検証してから OAuth まで案内します。

```powershell
.\.venv\Scripts\python.exe main.py setup-google
```

すでに `credentials.json` を自分で置いた場合のみ:

```powershell
.\.venv\Scripts\python.exe main.py auth
```

ブラウザが開いて Google 認証 → `token.json` が生成される。

#### 7. 動作確認

```powershell
.\.venv\Scripts\python.exe main.py sync --dry-run
.\.venv\Scripts\python.exe main.py sync
```

#### 8. 自動実行を設定

[USER_GUIDE のステップ8](USER_GUIDE.md#ステップ8-自動実行3時間ごとの設定) を参照。
パス（`プログラム/スクリプト` と `開始（オプション）`）は **自分のフォルダ位置** に書き換える必要があります。

---

## よくある質問

### Q. 配布元の `credentials.json` を使い回せませんか？

技術的には可能ですが、推奨しません。
- 配布元の Google Cloud プロジェクトのテストユーザーに毎回追加してもらう必要がある（最大100名）
- 配布元の責任で他人のカレンダーにアクセスできてしまう構造になる
- OAuth 同意画面が「配布元の名前」で表示されて怪しまれる

各自で自分のプロジェクトを作るのが安全で確実です。

### Q. 配布元の `accounts.yml` を渡されたらどうすればいい？

**Chatwork トークンは個人の鍵なので、即座にあなた自身のものに書き換えてください。**
他人のトークンを使うと、そのトークンの持ち主のカレンダーにあなたの権限で書き込むことになり、トラブルのもとです。

### Q. 配布元と同じ Chatwork アカウントを使いたい場合は？

`accounts.yml` に同じトークンを書けば動きますが、**同じカレンダーに重複登録されることになります**（Google アカウントが違えば違うカレンダーですが、同じ Google アカウントだと衝突する可能性あり）。
基本的にツールは「1人 = 1セットアップ」を想定しています。

### Q. Mac でも動きますか？

技術的には可能ですが、このマニュアルは Windows 前提で書かれています。Mac で動かす場合:
- Python のインストール: `brew install python` か公式インストーラ
- パスの書き方: `\` ではなく `/`
- 仮想環境の有効化: `source .venv/bin/activate`
- Windows タスクスケジューラの代わりに **launchd** または **cron** で定期実行

### Q. 複数人が同じPCで使えますか？

可能です。各自が別フォルダ（例: `task_scheduler_alice` / `task_scheduler_bob`）にコピーして、それぞれ別の `accounts.yml` / `credentials.json` を入れれば独立して動きます。
タスクスケジューラのタスクも別名で2つ作る必要があります。

### Q. アップデート（コードの更新）はどうすればいい？

Git で配布している場合は `git pull`。ZIP の場合は新しい ZIP を解凍して、古いフォルダの個人情報ファイル（`.env` `accounts.yml` `credentials.json` `token.json` `sync_state.db`）を新しいフォルダに **コピー** すれば、設定を引き継いで使えます。

---

## チェックリスト（配布する側）

ZIP で配布する前にチェック:

- [ ] `.venv/` フォルダを削除した
- [ ] `.env` を削除した
- [ ] `accounts.yml` を削除した
- [ ] `credentials.json` を削除した
- [ ] `token.json` を削除した
- [ ] `sync_state.db` を削除した
- [ ] `__pycache__/` フォルダを削除した
- [ ] `.env.example` と `accounts.yml.example` は残っている
- [ ] `USER_GUIDE.md` と `DISTRIBUTION.md` を一緒に渡す

## チェックリスト（受け取る側）

- [ ] Python 3.10 以上をインストールした
- [ ] フォルダを好きな場所に置いた
- [ ] `.env.example` をコピーして `.env` を作った
- [ ] `accounts.yml.example` をコピーして `accounts.yml` を作り、自分のトークンとIDを書いた
- [ ] 自分の Google Cloud プロジェクトを作り、`setup-google` で進めた **または** `credentials.json` を自分で配置した
- [ ] `python -m venv .venv` と `pip install -r requirements.txt` を実行した
- [ ] `python main.py setup-google` で Google 手順を進めた **または** `python main.py auth` で Google 認証した
- [ ] `python main.py sync --dry-run` でエラーが出ないことを確認した
- [ ] `python main.py sync` でカレンダーに予定が入った
- [ ] タスクスケジューラに登録した
