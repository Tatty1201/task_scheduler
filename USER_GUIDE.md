# 利用マニュアル（はじめての方向け）

このツールは、**Chatworkで自分に割り当てられたタスクをGoogle Calendarへ自動登録する**ためのものです。

プログラミング経験がなくても使えるように、最初から順番に説明します。

## 最初に必要なもの

- Windows / macOS / Linux のPC
- Python 3.10以上
- ChatworkアカウントとAPIトークン
- Googleアカウント

> Chatworkの「アカウントID」は不要です。必要なのはAPIトークンだけです。

---

## 1. Pythonをインストール

Python 3.10以上をインストールしてください。

インストール後、ターミナルまたはPowerShellで確認します。

```bash
python --version
```

`Python 3.10` 以上が表示されればOKです。

Windowsでは、Pythonインストール時に **Add python.exe to PATH** を有効にしておくと簡単です。

---

## 2. task_schedulerを取得

GitHubからcloneします。

```bash
git clone https://github.com/Tatty1201/task_scheduler.git
cd task_scheduler
```

Gitを使わない場合は、GitHubからZIPを取得して展開しても構いません。

---

## 3. 仮想環境を作成

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

依存ライブラリを入れます。

```bash
pip install -r requirements.txt
```

---

## 4. Chatwork APIトークンを取得

Chatworkにログインし、APIトークンを発行してください。

取得したトークンはパスワードと同じように扱い、他人に見せないでください。

このツールでは **Chatwork APIトークンだけを使います。アカウントIDを調べる必要はありません。**

---

## 5. 設定ファイルを作成

`.env.example` と `accounts.yml.example` をコピーします。

### Windows PowerShell

```powershell
Copy-Item .env.example .env
Copy-Item accounts.yml.example accounts.yml
```

### macOS / Linux

```bash
cp .env.example .env
cp accounts.yml.example accounts.yml
```

`accounts.yml` を開いて、Chatwork APIトークンを入力します。

```yaml
accounts:
  - name: main
    chatwork_api_token: ここにAPIトークン
```

複数のChatworkアカウントをまとめたい場合は追加できます。

```yaml
accounts:
  - name: main
    chatwork_api_token: トークン1

  - name: client_a
    chatwork_api_token: トークン2
```

`name` は内部識別用です。半角英数字・`_`・`-` を使い、それぞれ違う名前にしてください。

以前のバージョンで使っていた `chatwork_my_account_id` が残っていても、そのままで動きます。現在は使っていません。

---

## 6. Google Calendar APIを準備

Google Calendarへ予定を書き込むため、初回だけGoogle Cloud側の準備が必要です。

まず以下を実行してください。

```bash
python main.py setup-google
```

セットアップウィザードが、Google Cloud Consoleで必要なページを順番に案内します。

大まかな流れは以下です。

1. Google Cloudでプロジェクトを作成
2. Google Calendar APIを有効化
3. OAuth同意画面を設定
4. OAuth Client IDを **Desktop App** として作成
5. JSONをダウンロード
6. ファイル名を `credentials.json` にしてtask_scheduler直下へ置く
7. OAuth認証を実行

ウィザードを使わず手動で認証する場合は、`credentials.json` を置いたあとに実行します。

```bash
python main.py auth
```

ブラウザが開いたら、自分のGoogleアカウントで許可してください。

> `credentials.json` と認証後に作られる `token.json` は他人に共有しないでください。

---

## 7. まずDry runで確認

いきなりGoogle Calendarへ書き込まず、取得内容だけ確認します。

```bash
python main.py sync --dry-run
```

`[dry-run] insert:` のようなログが表示されれば、Chatworkからタスクを取得できています。

自分に割り当てられた未完了タスクが0件の場合は、エラーにならず0件として終了します。

---

## 8. 本番同期

```bash
python main.py sync
```

Google Calendarを開き、Chatworkタスクが予定として追加されていれば成功です。

### 日時の決まり方

- 時刻まで期限あり → その期限時刻から開始
- 日付だけ期限あり → その日の `DEFAULT_START_TIME` から開始
- 期限なし → タスク元メッセージ投稿日の `DEFAULT_START_TIME` から開始

予定の長さは `DEFAULT_DURATION_MIN` で決まります。

`.env` の既定値:

```dotenv
GOOGLE_CALENDAR_ID=primary
TIMEZONE=Asia/Tokyo
DEFAULT_START_TIME=10:00
DEFAULT_DURATION_MIN=60
LOG_LEVEL=INFO
```

---

## 9. 定期実行する

### Windows

Windowsの「タスク スケジューラ」で、定期的に以下を実行します。

プログラム:

```text
C:\path\to\task_scheduler\.venv\Scripts\python.exe
```

引数:

```text
main.py sync
```

開始フォルダ:

```text
C:\path\to\task_scheduler
```

たとえば3時間ごとに実行すれば、Chatworkに増えたタスクを定期的にCalendarへ追加できます。

macOS / LinuxではcronなどのOS標準スケジューラを利用できます。

---

## よく使うコマンド

| コマンド | 内容 |
|---|---|
| `python main.py setup-google` | Google OAuthセットアップを案内 |
| `python main.py auth` | Google認証のみ実行 |
| `python main.py sync --dry-run` | 書き込まず同期内容を確認 |
| `python main.py sync` | Google Calendarへ同期 |
| `python main.py reset` | ローカル同期履歴を初期化 |

`reset` を実行してもGoogle Calendar上のイベントは削除しません。

---

## 大事な仕様: 一度登録した予定は上書きしない

このツールは **insert-only** です。

一度ChatworkタスクをGoogle Calendarへ登録したあと、Calendar側で時間やタイトルを変更しても、その変更を同期ツールが元に戻すことはありません。

その代わり、Chatwork側で後から期限や本文を変更しても、既に作られたCalendarイベントには自動反映しません。

---

## 絶対に公開しないもの

以下はGitHub、Issue、Slack、SNSなどへ貼らないでください。

- Chatwork APIトークン
- `accounts.yml`
- `credentials.json`
- `token.json`
- `.env` に秘密情報を追加した場合はその内容

これらは `.gitignore` でGit管理から除外されています。

もし誤って公開した場合は、ファイルを消すだけではなく、該当するトークンや認証情報を失効・再発行してください。

---

## うまくいかなかったら

GitHub Issuesで報告してください。

報告時にあると助かる情報:

- OS
- Pythonバージョン
- 実行したコマンド
- エラーメッセージ
- どの手順で止まったか

**APIトークン、OAuth認証情報、Chatworkの個人情報・メッセージ本文は必ず削除してから投稿してください。**

第三者によるfresh-install検証も募集しています。初めて使って詰まった場所そのものが、ドキュメント改善の重要なフィードバックです。
