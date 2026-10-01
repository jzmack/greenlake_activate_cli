from typer.testing import CliRunner

from glcli import cli


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_query_rule_by_folder_id(monkeypatch):
    runner = CliRunner()
    session = FakeSession()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)
    monkeypatch.setattr(cli, "query_rule", lambda active_session, folder_id: captured.update(
        folder_id=folder_id
    ) or [{"ruleId": "63111165"}])
    monkeypatch.setattr(cli, "display_rules", lambda rules: captured.update(rules=rules))

    result = runner.invoke(cli.app, ["query", "rule", "folder-id", "63111131"])

    assert result.exit_code == 0
    assert captured["folder_id"] == "63111131"
    assert captured["rules"] == [{"ruleId": "63111165"}]
    assert session.closed is True


def test_query_rule_by_folder_name_resolves_one_id(monkeypatch):
    runner = CliRunner()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())
    monkeypatch.setattr(
        cli,
        "resolve_folder_ids",
        lambda active_session, values: captured.update(values=values) or ["63111131"],
    )
    monkeypatch.setattr(cli, "query_rule", lambda active_session, folder_id: captured.update(
        folder_id=folder_id
    ) or [])
    monkeypatch.setattr(cli, "display_rules", lambda rules: None)

    result = runner.invoke(cli.app, ["query", "rule", "folder-name", "Northwest"])

    assert result.exit_code == 0
    assert captured["values"] == ["Northwest"]
    assert captured["folder_id"] == "63111131"


def test_query_rule_folder_name_reports_unknown_folder(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())
    monkeypatch.setattr(
        cli,
        "resolve_folder_ids",
        lambda active_session, values: (_ for _ in ()).throw(ValueError("Folder(s) not found: Unknown")),
    )

    result = runner.invoke(cli.app, ["query", "rule", "folder-name", "Unknown"])

    assert result.exit_code != 0
    assert "Folder(s) not found: Unknown" in result.stderr
