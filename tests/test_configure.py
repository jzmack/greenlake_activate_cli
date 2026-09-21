from typer.testing import CliRunner

from glcli import cli
from glcli.activate_login import load_credentials, user_config_path


def test_save_user_credential_uses_user_config(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    config_path = cli.save_user_credential("  secret-token  ")

    assert config_path == user_config_path()
    assert config_path.read_text() == "CREDENTIAL_1=secret-token\n"
    assert load_credentials() == "secret-token"
    assert config_path.stat().st_mode & 0o777 == 0o600
    assert config_path.parent.stat().st_mode & 0o777 == 0o700


def test_configure_prompts_and_saves_credential(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    runner = CliRunner()

    result = runner.invoke(cli.app, ["configure"], input="secret-token\nsecret-token\n")

    assert result.exit_code == 0
    assert "Credential saved to" in result.stdout
    assert load_credentials() == "secret-token"
    assert "secret-token" not in result.stdout
