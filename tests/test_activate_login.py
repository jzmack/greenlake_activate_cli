import os

import pytest

from glcli.activate_login import load_credentials, user_config_path


def test_environment_variable_takes_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("CREDENTIAL_1", "  environment-token  ")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("CREDENTIAL_1=local-token\n")
    config_path = user_config_path()
    config_path.parent.mkdir(parents=True)
    config_path.write_text("CREDENTIAL_1=user-token\n")

    assert load_credentials() == "environment-token"


def test_user_config_is_used_when_environment_is_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("CREDENTIAL_1", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.chdir(tmp_path)
    config_path = user_config_path()
    config_path.parent.mkdir(parents=True)
    config_path.write_text("CREDENTIAL_1=user-token\n")

    assert load_credentials() == "user-token"


def test_project_local_config_is_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("CREDENTIAL_1", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "missing-config"))
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("CREDENTIAL_1=local-token\n")

    assert load_credentials() == "local-token"


def test_missing_credential_error_lists_supported_sources(monkeypatch, tmp_path):
    monkeypatch.delenv("CREDENTIAL_1", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="CREDENTIAL_1 is not configured") as error:
        load_credentials()

    assert "local-token" not in str(error.value)
    assert str(tmp_path / "config" / "greenlake-activate-cli" / ".env") in str(error.value)
    assert str(tmp_path / ".env") in str(error.value)


def test_loading_config_does_not_modify_environment(monkeypatch, tmp_path):
    monkeypatch.delenv("CREDENTIAL_1", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.chdir(tmp_path)
    config_path = user_config_path()
    config_path.parent.mkdir(parents=True)
    config_path.write_text("CREDENTIAL_1=user-token\n")

    assert load_credentials() == "user-token"
    assert "CREDENTIAL_1" not in os.environ
