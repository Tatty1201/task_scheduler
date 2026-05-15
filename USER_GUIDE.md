# 利用マニュアル（はじめての方向け）

このツールは **Chatwork で自分が担当のタスクを Google カレンダーに自動登録する** ものです。
3時間ごとに自動でカレンダーに予定を追加してくれます。

このマニュアルはコーディング未経験の方でも進められるように書いてあります。
**所要時間: 約30〜60分**

---

## 全体の流れ

1. 必要なソフトをインストール
2. ツールのフォルダを置く
3. Chatwork の API トークンを取得
4. Google アカウントで認証する準備
5. 設定ファイルを書く
6. 動作確認
7. 自動実行を設定

---

## ステップ1: Python をインストール

Python（パイソン）というプログラミング言語の実行環境が必要です。

1. [Python 公式サイト](https://www.python.org/downloads/windows/) にアクセス
2. 「Download Python 3.x.x」（数字は3.10以上）の黄色いボタンをクリック
3. ダウンロードしたインストーラを実行
4. **必ずチェック！**: インストール画面の一番下にある **「Add python.exe to PATH」** にチェックを入れる
5. 「Install Now」をクリック

### 確認

PowerShell（スタートメニューで「PowerShell」と検索）を開いて以下を入力:

```powershell
python --version
```

`Python 3.x.x` と表示されればOKです。

---

## ステップ2: ツールのフォルダを置く

ツール一式（`task_scheduler` というフォルダ）を、わかりやすい場所に置きます。

**おすすめの置き場所:**
```
C:\Users\(あなたのユーザー名)\Documents\task_scheduler
```

または、お使いの環境に合わせた場所でも構いません。

> ※ コード配布を受け取る方法については [DISTRIBUTION.md](DISTRIBUTION.md) を参照してください。

---

## ステップ3: Chatwork API トークンを取得

Chatwork が「このツールが Chatwork を見ていいですよ」と認める鍵を作ります。

1. Chatwork にブラウザでログイン
2. [API トークン取得ページ](https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php) を開く
3. ログインパスワードを入れて「表示」をクリック
4. 表示された **API トークン** をコピーしておく（後で使います）

> ⚠️ このトークンは**他人に教えないでください**。Chatwork を勝手に操作できる鍵です。

---

## ステップ4: Chatwork のアカウントID を取得

「数字のID」が必要です。プロフィール画面の英字IDではないので注意。

### 取り方

1. PowerShell で `task_scheduler` フォルダに移動:
   ```powershell
   cd "C:\Users\あなたのユーザー名\Documents\task_scheduler"
   ```
2. 仮想環境セットアップ（後のステップ7で詳しく）が済んでいれば、以下で確認できます:
   ```powershell
   .\.venv\Scripts\python.exe -c "import requests; print(requests.get('https://api.chatwork.com/v2/me', headers={'X-ChatWorkToken': 'ここにAPIトークンを貼る'}).json()['account_id'])"
   ```

または、**Chatwork の任意のチャットで自分宛てにメンションを書く**と、入力欄に `[To:1234567]` のようなタグが出ます。`To:` の後の数字があなたのアカウントIDです。

---

## ステップ5: Google アカウントの設定（一番ややこしい）

ツールが Google カレンダーに書き込めるように、Google 側で許可を出す手続きをします。

### 半自動ウィザード（おすすめ）

**ステップ7の `pip install` まで終わったあと**（仮想環境とライブラリが入った状態で）、同じフォルダで次を実行すると、必要な Google Cloud のページをブラウザで順に開き、`credentials.json` の中身を自動チェックし、続けて OAuth 認証まで案内します。

```powershell
cd "C:\Users\あなたのユーザー名\Documents\task_scheduler"
.\.venv\Scripts\python.exe main.py setup-google
```

- ブラウザを自動で開きたくない場合: `main.py setup-google --no-browser`（URLだけ表示）
- OAuth 認証はあとで自分でやる場合: `main.py setup-google --skip-auth`

ウィザードで詰まったときは、下の **5-1〜5-4** を手順書として読み替えてください。

> 手順の**理解**はこのステップ5で進め、**コマンド実行**はステップ7のあとで行うのがおすすめです。

---

### 5-1. Google Cloud のプロジェクトを作る

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス（Google でログイン）
2. 上部の **プロジェクト選択** をクリック → **「新しいプロジェクト」**
3. プロジェクト名: 任意（例: `task-scheduler`）→ 作成
4. プロジェクトが作られたら、画面上部のドロップダウンでそのプロジェクトを選択

### 5-2. Google カレンダーAPI を有効にする

1. 左メニューの **「APIとサービス」→「ライブラリ」**
2. 検索ボックスに `Google Calendar API` と入力
3. 出てきた「Google Calendar API」をクリック →「有効にする」

### 5-3. OAuth 同意画面を作る

1. 左メニューの **「APIとサービス」→「OAuth 同意画面」**（または「Google Auth Platform」）
2. **「外部」** を選択 → 作成
3. **アプリ情報**:
   - アプリ名: 任意（例: `task_scheduler`）
   - ユーザーサポートメール: 自分の Gmail
   - デベロッパー連絡先: 自分の Gmail
   - 「次へ」「次へ」「保存して次へ」と進む
4. **テストユーザー**:
   - **必ず自分の Gmail アドレスを追加**（しないと後で「アクセスをブロック」エラーになります）
5. 「保存して次へ」「ダッシュボードに戻る」

### 5-4. 認証情報（credentials.json）を作る

1. 左メニューの **「APIとサービス」→「認証情報」**（または「クライアント」）
2. 上部の **「+ 認証情報を作成」→「OAuth クライアントID」**
3. **アプリケーションの種類**: **「デスクトップアプリ」** を選択
4. 名前: 任意 → 作成
5. 作成後のダイアログまたは一覧から **「JSONをダウンロード」**
6. ダウンロードしたファイル（`client_secret_xxxxx.json` のような名前）を:
   - **`credentials.json`** に名前を変更
   - **`task_scheduler` フォルダの直下**に置く（`main.py` と同じ場所）

> ⚠️ `credentials.json` も他人に渡さないでください。

---

## ステップ6: 設定ファイルを書く

`task_scheduler` フォルダの中で、2つの設定ファイルを作ります。

### 6-1. `.env` ファイル

`task_scheduler` フォルダにある **`.env.example`** をコピーして、名前を **`.env`** に変えます。

中身は基本そのままで大丈夫です。タイムゾーンや時刻のデフォルト値を変えたい場合だけ編集します。

### 6-2. `accounts.yml` ファイル

`accounts.yml.example` をコピーして、名前を **`accounts.yml`** に変えます。

メモ帳などで開いて、こう書きます:

```yaml
accounts:
  - name: main
    chatwork_api_token: ここにステップ3でコピーしたトークンを貼る
    chatwork_my_account_id: ここにステップ4で取得したアカウントID（数字）
```

複数のChatworkアカウントを同期したい場合は、項目を追加できます:

```yaml
accounts:
  - name: main
    chatwork_api_token: トークン1
    chatwork_my_account_id: 1234567

  - name: client_a
    chatwork_api_token: トークン2
    chatwork_my_account_id: 7654321
```

`name` は内部識別用の名前です（半角英数・アンダースコア・ハイフンのみ、ユニークに）。
カレンダーには表示されません。

> ⚠️ `accounts.yml` と `.env` は他人に渡さないでください。

---

## ステップ7: 仮想環境を作って動かす

PowerShell で `task_scheduler` フォルダに移動して、3つのコマンドを順番に実行します。

```powershell
cd "C:\Users\あなたのユーザー名\Documents\task_scheduler"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

最後のコマンドは数十秒〜数分かかります。エラーなく終わればOK。

### Google 認証（初回のみ）

**おすすめ:** ステップ5の手順をブラウザで順に案内してくれるウィザードを使います（`credentials.json` の形式チェック付き）。

```powershell
.\.venv\Scripts\python.exe main.py setup-google
```

ウィザードの最後で OAuth 認証まで済ませた場合は、下の `main.py auth` は **不要** です。

**手動で済ませたい場合**（`credentials.json` をすでに置いているとき）:

```powershell
.\.venv\Scripts\python.exe main.py auth
```

ブラウザが開きます。**ステップ5-3 でテストユーザーに追加した Gmail でログイン** → 「許可」をクリック → 「認証は完了しました」と出ればOK。

> 「アクセスをブロック」と出たら、ステップ5-3 の **テストユーザー追加を忘れている** 可能性が高いです。Google Cloud Console の OAuth 同意画面でテストユーザーに自分の Gmail を追加してください。

### お試し（カレンダーには書き込まない）

```powershell
.\.venv\Scripts\python.exe main.py sync --dry-run
```

「[dry-run] insert: ...」のような行が出れば、設定は完璧です。

### 本番実行

```powershell
.\.venv\Scripts\python.exe main.py sync
```

Google カレンダーを開いて、Chatwork のタスクが予定として入っていれば成功です。

---

## ステップ8: 自動実行（3時間ごと）の設定

### Windows タスクスケジューラに登録

1. スタートメニューで **「タスクスケジューラ」** を検索して起動
2. 右ペインの **「タスクの作成」** をクリック（「基本タスクの作成」ではなく）

#### 「全般」タブ
- **名前**: `Chatwork → Google Calendar 同期`
- **「ユーザーがログオンしているときのみ実行する」** を選択（パスワード入力が不要になります）

#### 「トリガー」タブ → 新規
- 開始: 任意の日付の `0:00:00`
- 「毎日」を選択
- **「詳細設定」** → **「繰り返し間隔」** に `3 時間` と入力（プルダウンに無くても直接入力可）
- 「継続時間」: 「無期限」
- OK

#### 「操作」タブ → 新規
- **プログラム/スクリプト**:
  ```
  C:\Users\あなたのユーザー名\Documents\task_scheduler\.venv\Scripts\python.exe
  ```
- **引数の追加**:
  ```
  main.py sync
  ```
- **開始（オプション）**: ⚠️**ここ重要**
  ```
  C:\Users\あなたのユーザー名\Documents\task_scheduler
  ```
  これを設定しないと設定ファイルを読めず失敗します。

#### 「条件」タブ
- 「コンピュータをAC電源で使用している場合のみ」のチェックを外す（バッテリー駆動でも動くように）

### 動作テスト

タスクスケジューラの一覧から作ったタスクを **右クリック →「実行する」**
→ 「最後の実行結果」が **「(0x0)」** なら成功

---

## カレンダーに登録されたあとは

- カレンダー上で **ドラッグして時間を動かしてOK** です
- ツールは「**一度登録したタスクは二度と更新しない**」設計なので、移動した予定が同期で元に戻ったりしません
- Chatwork でタスクを完了しても、カレンダー上の予定は残ります（履歴として）
- 不要になった予定は手動で削除してください

---

## よくある質問

### Q. iPhone / Mac の Apple カレンダーアプリで見れますか？

iPhone や Mac の **設定で Google アカウントを追加** すれば、Apple カレンダーアプリでも Google カレンダーの予定が見られます。このツールは Google カレンダーに書き込むので、iPhone でも自動で同じ予定が見えます。

- **iPhone**: 設定 → カレンダー → アカウント → アカウントを追加 → Google
- **Mac**: システム設定 → インターネットアカウント → Google

### Q. Chatwork で完了したタスクはカレンダーから消えますか？

消えません（仕様）。「やり終わった履歴」としてカレンダーに残ります。不要なら手動で削除してください。

### Q. PCを起動していない時間（深夜など）はどうなりますか？

その時間のスケジュール実行はスキップされます。次に PC が起動して同期が走ったときに、そのときオープンになっているタスクをまとめて取得・登録します。タスクが消えることはありません。

### Q. うまく動かない時はどこを見ればいい？

PowerShell で手動実行（`python main.py sync`）してエラーメッセージを確認するのが一番確実です。ログには日本語でエラーの場所が書いてあります。

### Q. パスワードを入れる画面が出るのはなぜ？

タスクスケジューラで「ユーザーがログオンしているかどうかにかかわらず実行する」を選ぶと、Windows のサインイン用パスワードを聞かれます。ログオン中だけ動けばOKなら「ユーザーがログオンしているときのみ」を選べばパスワード入力は不要です。

---

## トラブル時の連絡先

技術的な不具合や設定で詰まった場合は、開発元に問い合わせてください。
問い合わせ時は **PowerShell に出たエラーメッセージのスクリーンショット** があると早く解決できます。
