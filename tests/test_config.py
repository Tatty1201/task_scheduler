from __future__ import annotations

from pathlib import Path

from src.config import _load_accounts


def test_account_only_requires_name_and_api_token(tmp_path: Path) -> None:
    config_path = tmp_path / "accounts.yml"
    config_path.write_text(
        """accounts:\n  - name: main\n    chatwork_api_token: test-token\n""",
        encoding="utf-8",
    )

    accounts = _load_accounts(config_path)

    assert len(accounts) == 1
    assert accounts[0].name == "main"
    assert accounts[0].api_token == "test-token"


def test_legacy_account_id_is_accepted_and_ignored(tmp_path: Path) -> None:
    config_path = tmp_path / "accounts.yml"
    config_path.write_text(
        """accounts:\n  - name: main\n    chatwork_api_token: test-token\n    chatwork_my_account_id: 1234567\n""",
        encoding="utf-8",
    )

    accounts = _load_accounts(config_path)

    assert len(accounts) == 1
    assert accounts[0].name == "main"
    assert accounts[0].api_token == "test-token"
    assert not hasattr(accounts[0], "my_account_id")
