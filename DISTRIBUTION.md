# 配布・別PCへの導入ガイド

このツールを別の人・別のPCで使うときの基本方針をまとめます。

## 大原則

**コードは共有してOK。認証情報は共有しない。**

共有してよいもの:

- GitHub上のソースコード
- `requirements.txt`
- `.env.example`
- `accounts.yml.example`
- READMEや各種ドキュメント

共有してはいけないもの:

- `.env`
- `accounts.yml`
- `credentials.json`
- `token.json`
- `sync_state.db`
- 実際のChatwork APIトークン

これらは `.gitignore` で除外しています。

## おすすめの配布方法

GitHubの公開リポジトリから、利用者本人にcloneまたはZIP取得してもらう方法を推奨します。

```bash
git clone https://github.com/Tatty1201/task_scheduler.git
cd task_scheduler
```

こうすると、コードと認証情報を分離したまま更新履歴も追えます。

## 利用者が自分で用意するもの

各利用者は、自分の環境で以下を用意します。

1. Python 3.10以上
2. 自分のChatwork APIトークン
3. 自分のGoogleアカウント
4. 自分のGoogle Cloud OAuth Client

**ChatworkのアカウントIDは不要です。**

## 別PCでのセットアップ

### 1. 仮想環境と依存関係

```bash
python -m venv .venv
```

仮想環境を有効化後:

```bash
pip install -r requirements.txt
```

### 2. ローカル設定を作る

Windows PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item accounts.yml.example accounts.yml
```

macOS / Linux:

```bash
cp .env.example .env
cp accounts.yml.example accounts.yml
```

`accounts.yml`:

```yaml
accounts:
  - name: main
    chatwork_api_token: 利用者本人のAPIトークン
```

複数アカウントの場合:

```yaml
accounts:
  - name: main
    chatwork_api_token: トークン1

  - name: client_a
    chatwork_api_token: トークン2
```

以前の設定に `chatwork_my_account_id` が残っていても問題ありません。現在は使わないため無視されます。

### 3. Google OAuth

```bash
python main.py setup-google
```

利用者本人のGoogle CloudプロジェクトでOAuth Clientを作成し、ダウンロードしたJSONを `credentials.json` として配置します。

認証後に作られる `token.json` も、その利用者のPCだけに保存します。

### 4. Dry run

```bash
python main.py sync --dry-run
```

### 5. 本番同期

```bash
python main.py sync
```

## 定期実行

### Windows

Windows Task Schedulerから、プロジェクトの仮想環境Pythonで以下を定期実行します。

```text
main.py sync
```

「開始」フォルダはtask_schedulerのプロジェクト直下にしてください。

### macOS / Linux

cronなど、OS標準の定期実行機能から同じコマンドを実行できます。

## 更新するとき

Git cloneで導入している場合は、ローカル設定を保持したままコードだけ更新できます。

```bash
git pull
pip install -r requirements.txt
```

`.env`、`accounts.yml`、`credentials.json`、`token.json` はGit管理されていないため通常はそのまま残ります。

更新前後でCHANGELOGも確認してください。

## 配布前・Issue投稿前の安全確認

- [ ] Chatwork APIトークンが含まれていない
- [ ] `accounts.yml` が含まれていない
- [ ] `credentials.json` が含まれていない
- [ ] `token.json` が含まれていない
- [ ] `.env` に秘密情報がある場合、それが含まれていない
- [ ] ログやスクリーンショットに個人情報が写っていない

認証情報を誤って公開した場合は、Gitから削除するだけでなく、必ず該当するトークンやOAuth認証情報を失効・再発行してください。

詳しい初回導入は [USER_GUIDE.md](USER_GUIDE.md) を参照してください。
