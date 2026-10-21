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


def test_serial_command_accepts_file_without_positional_serial(monkeypatch, tmp_path):
    runner = CliRunner()
    captured = {}

    serial_file = tmp_path / "serials.txt"
    serial_file.write_text("SN1\nSN2\n")

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())
    monkeypatch.setattr(
        cli,
        "read_identifiers_from_file",
        lambda path, identifier_type: ["SN1", "SN2"],
    )

    def fake_query(active_session, identifier_type, identifiers):
        captured["query"] = (identifier_type, identifiers)
        return '{"devices": [{"serialNumber": "SN1"}]}', []

    monkeypatch.setattr(cli, "query_inventory", fake_query)
    monkeypatch.setattr(cli, "display_inventory_sn", lambda data: None)

    result = runner.invoke(cli.app, ["query", "serial", "--file", str(serial_file)])

    assert result.exit_code == 0
    assert captured["query"] == ("serial", ["SN1", "SN2"])


def test_mac_command_accepts_file_without_positional_mac(monkeypatch, tmp_path):
    runner = CliRunner()
    captured = {}

    mac_file = tmp_path / "macs.txt"
    mac_file.write_text("aa:bb:cc:00:11:22\ndd:ee:ff:33:44:55\n")

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())
    monkeypatch.setattr(
        cli,
        "read_identifiers_from_file",
        lambda path, identifier_type: ["AA:BB:CC:00:11:22", "DD:EE:FF:33:44:55"],
    )

    def fake_query(active_session, identifier_type, identifiers):
        captured["query"] = (identifier_type, identifiers)
        return '{"devices": [{"mac": "AA:BB:CC:00:11:22"}]}', []

    monkeypatch.setattr(cli, "query_inventory", fake_query)
    monkeypatch.setattr(cli, "display_inventory_sn", lambda data: None)

    result = runner.invoke(cli.app, ["query", "mac", "--file", str(mac_file)])

    assert result.exit_code == 0
    assert captured["query"] == (
        "mac",
        ["AA:BB:CC:00:11:22", "DD:EE:FF:33:44:55"],
    )


def test_folder_command_queries_numeric_ids(monkeypatch):
    runner = CliRunner()
    captured = {}
    session = FakeSession()

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)

    def fake_query(active_session, identifier_type, identifiers):
        captured["query"] = (identifier_type, identifiers)
        return '{"devices": [{"serialNumber": "SN1"}]}', []

    monkeypatch.setattr(cli, "query_inventory", fake_query)
    monkeypatch.setattr(cli, "display_inventory_sn", lambda data: None)

    result = runner.invoke(cli.app, ["query", "folder", "5297450", "5389522"])

    assert result.exit_code == 0
    assert captured["query"] == ("folder", ["5297450", "5389522"])
    assert session.closed is True


def test_folder_command_resolves_names_before_query(monkeypatch):
    runner = CliRunner()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: FakeSession())
    monkeypatch.setattr(cli, "resolve_folder_ids", lambda session, values: ["5297450"])

    def fake_query(active_session, identifier_type, identifiers):
        captured["query"] = (identifier_type, identifiers)
        return '{"devices": [{"serialNumber": "SN1"}]}', []

    monkeypatch.setattr(cli, "query_inventory", fake_query)
    monkeypatch.setattr(cli, "display_inventory_sn", lambda data: None)

    result = runner.invoke(cli.app, ["query", "folder", "SiteA-South"])

    assert result.exit_code == 0
    assert captured["query"] == ("folder", ["5297450"])


def test_query_reports_missing_credentials(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "load_credentials",
        lambda: (_ for _ in ()).throw(RuntimeError("CREDENTIAL_1 is not configured")),
    )

    result = runner.invoke(cli.app, ["query", "serial", "SN1"])

    assert result.exit_code != 0
    assert "CREDENTIAL_1 is not configured" in result.stderr


def test_generate_rap_allowlist_from_file_confirms_and_prints_commands(tmp_path):
    runner = CliRunner()
    file_path = tmp_path / "allowlist.csv"
    file_path.write_text(
        "mac_address,ap_group,serial,description\n"
        "aa:bb:cc:00:11:22,remote,SN1,North site\n"
    )

    result = runner.invoke(
        cli.app,
        ["generate-allowlist", "rap", "file", str(file_path)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "allowlist-db rap add mac-address AA:BB:CC:00:11:22 ap-name SN1" in result.stdout
    assert 'description "North site"' in result.stdout


def test_generate_allowlist_file_decline_does_not_print_commands(tmp_path):
    runner = CliRunner()
    file_path = tmp_path / "allowlist.csv"
    file_path.write_text("mac_address,ap_group\naa:bb:cc:00:11:22,campus\n")

    result = runner.invoke(
        cli.app,
        ["generate-allowlist", "cap", "file", str(file_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "generation cancelled" in result.stdout
    assert "allowlist-db cpsec add" not in result.stdout


def test_generate_allowlist_text_option_writes_commands_to_file(tmp_path, monkeypatch):
    runner = CliRunner()
    file_path = tmp_path / "allowlist.csv"
    file_path.write_text("mac_address,ap_group\naa:bb:cc:00:11:22,campus\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        cli.app,
        ["generate-allowlist", "cap", "file", str(file_path), "--text"],
        input="y\n",
    )

    assert result.exit_code == 0
    assert (tmp_path / "allowlist_commands.txt").read_text() == (
        "allowlist-db cpsec add mac-address AA:BB:CC:00:11:22 ap-group campus\n"
    )
    assert "Wrote 1 command(s) to allowlist_commands.txt" in result.stdout
    assert "Generated allowlist commands:" not in result.stdout


def test_generate_allowlist_text_decline_preserves_existing_file(tmp_path, monkeypatch):
    runner = CliRunner()
    file_path = tmp_path / "allowlist.csv"
    file_path.write_text("mac_address,ap_group\naa:bb:cc:00:11:22,campus\n")
    output_path = tmp_path / "allowlist_commands.txt"
    output_path.write_text("keep this content\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        cli.app,
        ["generate-allowlist", "cap", "file", str(file_path), "--text"],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "overwrite existing file" in result.stdout
    assert output_path.read_text() == "keep this content\n"


def test_generate_cap_allowlist_from_folder_prompts_when_group_is_missing(monkeypatch):
    runner = CliRunner()
    session = FakeSession()

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)
    monkeypatch.setattr(cli, "resolve_folder_ids", lambda active_session, values: ["123"])
    monkeypatch.setattr(
        cli,
        "query_inventory",
        lambda active_session, identifier_type, identifiers: (
            '{"devices": [{"serialNumber": "SN1", "mac": "AA:BB:CC:00:11:22"}]}',
            [],
        ),
    )
    monkeypatch.setattr(cli, "query_rule", lambda active_session, folder_id: [])

    result = runner.invoke(
        cli.app,
        ["generate-allowlist", "cap", "folder", "Site A"],
        input="campus\ny\n",
    )

    assert result.exit_code == 0
    assert "No AP group is defined" in result.stdout
    assert "allowlist-db cpsec add mac-address AA:BB:CC:00:11:22 ap-group campus" in result.stdout
    assert session.closed is True


def test_generate_rap_allowlist_from_folder_uses_rule_group_and_serial(monkeypatch):
    runner = CliRunner()
    session = FakeSession()

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)
    monkeypatch.setattr(cli, "resolve_folder_ids", lambda active_session, values: ["123"])
    monkeypatch.setattr(
        cli,
        "query_inventory",
        lambda active_session, identifier_type, identifiers: (
            '{"devices": [{"serialNumber": "SN1", "mac": "AA:BB:CC:00:11:22"}]}',
            [],
        ),
    )
    monkeypatch.setattr(
        cli,
        "query_rule",
        lambda active_session, folder_id: [{"apGroup": "remote"}],
    )

    result = runner.invoke(
        cli.app,
        ["generate-allowlist", "rap", "folder", "Site A"],
        input="y\n",
    )

    assert result.exit_code == 0
    assert "allowlist-db rap add mac-address AA:BB:CC:00:11:22 ap-name SN1 ap-group remote" in result.stdout
    assert session.closed is True


def test_generate_allowlist_folder_rejects_multiple_ap_groups(monkeypatch):
    runner = CliRunner()
    session = FakeSession()

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)
    monkeypatch.setattr(cli, "resolve_folder_ids", lambda active_session, values: ["123"])
    monkeypatch.setattr(
        cli,
        "query_inventory",
        lambda active_session, identifier_type, identifiers: (
            '{"devices": [{"serialNumber": "SN1", "mac": "AA:BB:CC:00:11:22"}]}',
            [],
        ),
    )
    monkeypatch.setattr(
        cli,
        "query_rule",
        lambda active_session, folder_id: [{"apGroup": "campus"}, {"apGroup": "remote"}],
    )

    result = runner.invoke(
        cli.app,
        ["generate-allowlist", "cap", "folder", "Site A"],
    )

    assert result.exit_code != 0
    assert "multiple AP groups" in result.stderr
    assert session.closed is True
