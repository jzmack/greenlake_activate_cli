from typer.testing import CliRunner

from glcli import cli
from glcli.create_folder import CreatedFolder


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_create_folder_command_prints_created_folder(monkeypatch):
    runner = CliRunner()
    session = FakeSession()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)

    def fake_create_folder(active_session, folder_name):
        captured["call"] = (active_session, folder_name)
        return CreatedFolder("69832536", folder_name)

    monkeypatch.setattr(cli, "create_folder", fake_create_folder)

    result = runner.invoke(cli.app, ["create", "folder", "  Northwest  "])

    assert result.exit_code == 0
    assert captured["call"] == (session, "Northwest")
    assert "Created folder 'Northwest' with ID 69832536" in result.stdout
    assert session.closed is True


def test_create_folder_rejects_empty_name(monkeypatch):
    runner = CliRunner()

    result = runner.invoke(cli.app, ["create", "folder", "   "])

    assert result.exit_code != 0
    assert "folder name is required" in result.stderr
