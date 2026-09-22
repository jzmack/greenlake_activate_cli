from typer.testing import CliRunner

from glcli import cli


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_direct_serial_move_resolves_and_updates(monkeypatch):
    runner = CliRunner()
    session = FakeSession()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)
    monkeypatch.setattr(
        cli,
        "resolve_move_macs",
        lambda active_session, identifier_type, identifiers: (["AA:BB:CC:DD:EE:FF"], []),
    )
    monkeypatch.setattr(
        cli,
        "move_device",
        lambda active_session, macs, destination: captured.update(
            macs=macs, destination=destination
        ),
    )

    result = runner.invoke(cli.app, ["move", "SN1", "Northwest"])

    assert result.exit_code == 0
    assert captured == {"macs": ["AA:BB:CC:DD:EE:FF"], "destination": "Northwest"}
    assert session.closed is True


def test_mac_file_move_uses_mac_identifier_type(monkeypatch, tmp_path):
    runner = CliRunner()
    captured = {}
    mac_file = tmp_path / "macs.txt"
    mac_file.write_text("aa:bb:cc:dd:ee:ff\n")

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())
    monkeypatch.setattr(cli, "read_identifiers_from_file", lambda path, kind: ["AA:BB:CC:DD:EE:FF"])
    monkeypatch.setattr(
        cli,
        "resolve_move_macs",
        lambda active_session, identifier_type, identifiers: (["AA:BB:CC:DD:EE:FF"], []),
    )
    monkeypatch.setattr(
        cli,
        "move_device",
        lambda active_session, macs, destination: captured.update(
            macs=macs, destination=destination
        ),
    )

    result = runner.invoke(cli.app, ["move", "macs", str(mac_file), "5297450"])

    assert result.exit_code == 0
    assert captured["macs"] == ["AA:BB:CC:DD:EE:FF"]
    assert captured["destination"] == "5297450"


def test_move_continues_with_valid_devices(monkeypatch):
    runner = CliRunner()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())
    monkeypatch.setattr(
        cli,
        "resolve_move_macs",
        lambda active_session, identifier_type, identifiers: (["AA:BB:CC:DD:EE:FF"], ["SN2"]),
    )
    monkeypatch.setattr(
        cli,
        "move_device",
        lambda active_session, macs, destination: captured.update(macs=macs),
    )

    result = runner.invoke(cli.app, ["move", "SN1", "Northwest"])

    assert result.exit_code == 2
    assert captured["macs"] == ["AA:BB:CC:DD:EE:FF"]
