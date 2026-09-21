from typer.testing import CliRunner

from glcli import cli


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_serial_command_accepts_multiple_values(monkeypatch):
    runner = CliRunner()
    session = FakeSession()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)

    def fake_query(active_session, identifier_type, identifiers):
        captured["query"] = (active_session, identifier_type, identifiers)
        return '{"devices": [{"serialNumber": "SN1"}]}', []

    monkeypatch.setattr(cli, "query_inventory", fake_query)
    monkeypatch.setattr(cli, "display_inventory_sn", lambda data: None)

    result = runner.invoke(cli.app, ["query", "serial", "SN1", "sn2"])

    assert result.exit_code == 0
    assert captured["query"] == (session, "serial", ["SN1", "SN2"])
    assert session.closed is True


def test_mac_command_passes_mac_values(monkeypatch):
    runner = CliRunner()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())

    def fake_query(active_session, identifier_type, identifiers):
        captured["query"] = (identifier_type, identifiers)
        return '{"devices": [{"mac": "AA:BB:CC:00:11:22"}]}', []

    monkeypatch.setattr(cli, "query_inventory", fake_query)
    monkeypatch.setattr(cli, "display_inventory_sn", lambda data: None)

    result = runner.invoke(cli.app, ["query", "mac", "aa:bb:cc:00:11:22", "dd:ee:ff:33:44:55"])

    assert result.exit_code == 0
    assert captured["query"] == (
        "mac",
        ["AA:BB:CC:00:11:22", "DD:EE:FF:33:44:55"],
    )
