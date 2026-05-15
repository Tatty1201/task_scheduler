"""Google Calendar API 用 OAuth の半自動セットアップウィザード。

Google Cloud Console の操作はユーザーが行う必要があるが、
必要なページをブラウザで開き、credentials.json の形式を検証し、
続けて OAuth 認証まで案内する。
"""
from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .google_calendar import authenticate
from .logger import setup_logger


logger = setup_logger(__name__)

# プロジェクト未選択時はプロジェクト選択が先に出る
URL_CALENDAR_API = (
    "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com"
)
URL_OAUTH_CONSENT = (
    "https://console.cloud.google.com/apis/credentials/consent"
)
URL_CREATE_CREDENTIALS = (
    "https://console.cloud.google.com/apis/credentials"
)


def validate_credentials_json(path: Path) -> tuple[bool, str]:
    """Desktop OAuth 用 credentials.json の形式を検証する。

    Returns:
        (True, "OK") または (False, 人間向けエラーメッセージ)
    """
    if not path.exists():
        return False, f"ファイルが見つかりません: {path}"

    try:
        raw_text = path.read_text(encoding="utf-8")
        data: Any = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return False, f"JSONとして読めません: {exc}"

    if not isinstance(data, dict):
        return False, "JSONのルートがオブジェクトではありません"

    if "installed" in data:
        inst = data["installed"]
        if not isinstance(inst, dict):
            return False, '"installed" がオブジェクトではありません'
        if not inst.get("client_id"):
            return False, '"installed.client_id" がありません'
        if not inst.get("client_secret"):
            return False, '"installed.client_secret" がありません'
        return True, "OK (デスクトップアプリ用 credentials.json)"

    if "web" in data:
        return (
            False,
            '"web" クライアントのJSONです。このツールは「デスクトップアプリ」用の'
            " credentials.json が必要です。Google Cloud で OAuth クライアント種別を"
            " デスクトップアプリにして JSON をダウンロードし直してください。",
        )

    return (
        False,
        '"installed" キーがありません。Google Cloud の「認証情報」で'
        " OAuth クライアントの種類が「デスクトップアプリ」になっているか確認してください。",
    )


def _pause(message: str) -> None:
    try:
        input(message)
    except EOFError:
        logger.warning("標準入力が使えない環境のためスキップします")


def run_setup_wizard(*, open_browser: bool = True, run_auth_after: bool = True) -> int:
    """対話型ウィザード。成功時 0、致命的エラー時 1。"""
    cred_path = PROJECT_ROOT / "credentials.json"
    token_path = PROJECT_ROOT / "token.json"

    print()
    print("=" * 60)
    print(" Google Calendar API / OAuth セットアップ（半自動）")
    print("=" * 60)
    print()
    print("このウィザードは次のことを行います。")
    print("  1. Google Cloud Console の該当ページをブラウザで開く（任意）")
    print("  2. 手順の説明を表示する")
    print("  3. credentials.json の形式をチェックする")
    print("  4. 問題なければ OAuth 認証（auth）まで進める（任意）")
    print()
    print("※ Google の仕様上、プロジェクト作成や「テストユーザー」追加は")
    print("  ブラウザで自分が操作する必要があります（完全自動はできません）。")
    print()

    # --- Step A: Calendar API ---
    print("[ステップ A] Google Calendar API を有効にする")
    print("  - まだ無ければ Google Cloud でプロジェクトを作成してください。")
    print("  - 次のページで「有効にする」をクリックします。")
    print()
    if open_browser:
        print(f"  開くURL: {URL_CALENDAR_API}")
        try:
            webbrowser.open(URL_CALENDAR_API)
        except Exception as exc:
            logger.warning("ブラウザを開けませんでした: %s", exc)
    _pause("  有効化が終わったら Enter を押してください… ")

    # --- Step B: OAuth consent ---
    print()
    print("[ステップ B] OAuth 同意画面（外部アプリ・テストユーザー）")
    print("  - User type: 外部")
    print("  - アプリ名・メールを入力して保存")
    print("  - 「テストユーザー」に、このツールで使う Gmail を必ず追加")
    print("    （追加しないと「アクセスをブロック」になります）")
    print()
    if open_browser:
        print(f"  開くURL: {URL_OAUTH_CONSENT}")
        try:
            webbrowser.open(URL_OAUTH_CONSENT)
        except Exception as exc:
            logger.warning("ブラウザを開けませんでした: %s", exc)
    _pause("  同意画面とテストユーザーを終えたら Enter を押してください… ")

    # --- Step C: Create OAuth client ---
    print()
    print("[ステップ C] OAuth クライアント ID を作成（デスクトップアプリ）")
    print("  - 「認証情報を作成」→「OAuth クライアント ID」")
    print("  - アプリケーションの種類: **デスクトップアプリ** を選ぶ（重要）")
    print("  - 作成後「JSON をダウンロード」")
    print(f"  - ダウンロードしたファイルを次の名前でこのフォルダに置く:")
    print(f"      {cred_path}")
    print("  - ファイル名を credentials.json にリネームする")
    print()
    if open_browser:
        print(f"  開くURL: {URL_CREATE_CREDENTIALS}")
        try:
            webbrowser.open(URL_CREATE_CREDENTIALS)
        except Exception as exc:
            logger.warning("ブラウザを開けませんでした: %s", exc)

    while True:
        _pause(
            "\n  credentials.json を置いたら Enter を押してください… "
            "(まだの場合も Enter で再チェック) "
        )
        ok, msg = validate_credentials_json(cred_path)
        if ok:
            print(f"\n  ✓ {msg}\n")
            break
        print(f"\n  ✗ {msg}\n")
        retry = input("  修正したら Enter / 中止は q + Enter: ").strip().lower()
        if retry == "q":
            print("セットアップを中止しました。")
            return 1

    if not run_auth_after:
        print("credentials.json は問題ありません。")
        print("続けて次を実行してください:")
        print("  python main.py auth")
        return 0

    print("[ステップ D] ブラウザで Google にログインし、カレンダーへのアクセスを許可")
    do_auth = input("  いま OAuth 認証を実行しますか？ [Y/n]: ").strip().lower()
    if do_auth in ("n", "no"):
        print("スキップしました。あとで次を実行してください:")
        print("  python main.py auth")
        return 0

    try:
        authenticate(cred_path, token_path)
    except Exception as exc:
        logger.exception("OAuth 認証に失敗: %s", exc)
        return 1

    logger.info("認証完了: %s", token_path)
    print()
    print("完了しました。次は Chatwork 設定後に同期できます:")
    print("  python main.py sync --dry-run")
    print("  python main.py sync")
    print()
    return 0
