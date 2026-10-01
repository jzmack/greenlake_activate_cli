from typer.testing import CliRunner

from glcli import cli
from glcli.create_rule import CreatedProvisionRule


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_create_rule_by_folder_id_prompts_maps_and_confirms(monkeypatch):
    runner = CliRunner()
    session = FakeSession()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)

    def fake_create(active_session, rule_name, folder_id, provision_type, controller, ap_group):
        captured["args"] = (active_session, rule_name, folder_id, provision_type, controller, ap_group)
        return CreatedProvisionRule("70081128", rule_name)

    monkeypatch.setattr(cli, "create_provision_rule", fake_create)
    result = runner.invoke(
        cli.app,
        ["create", "rule", "folder-id", "63061537"],
        input="test_rule\ncap\n10.103.6.18\nindoor\ny\n",
    )

    assert result.exit_code == 0
    assert captured["args"] == (
        session,
        "test_rule",
        "63061537",
        "iap_to_cap",
        "10.103.6.18",
        "indoor",
    )
    assert "Created provisioning rule 'test_rule' with ID 70081128" in result.stdout
    assert session.closed is True


def test_create_rule_by_folder_name_resolves_folder_before_confirmation(monkeypatch):
    runner = CliRunner()
    session = FakeSession()
    captured = {}

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)
    monkeypatch.setattr(
        cli,
        "resolve_folder_ids",
        lambda active_session, names: captured.update(names=names) or ["63061537"],
    )
    monkeypatch.setattr(
        cli,
        "create_provision_rule",
        lambda active_session, *args: captured.update(create_args=args)
        or CreatedProvisionRule("70081128", args[0]),
    )

    result = runner.invoke(
        cli.app,
        ["create", "rule", "folder-name", "Northwest"],
        input="test_rule\nrap\n10.103.6.18\nindoor\ny\n",
    )

    assert result.exit_code == 0
    assert captured["names"] == ["Northwest"]
    assert captured["create_args"] == (
        "test_rule",
        "63061537",
        "iap_to_rap",
        "10.103.6.18",
        "indoor",
    )
    assert session.closed is True


def test_declining_confirmation_does_not_create_rule(monkeypatch):
    runner = CliRunner()
    session = FakeSession()
    called = False

    monkeypatch.setattr(cli, "load_credentials", lambda: "token")
    monkeypatch.setattr(cli, "create_activate_session", lambda credential: session)

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(cli, "create_provision_rule", fail_if_called)
    result = runner.invoke(
        cli.app,
        ["create", "rule", "folder-id", "63061537"],
        input="test_rule\ncap\n10.103.6.18\nindoor\nn\n",
    )

    assert result.exit_code == 0
    assert "Rule creation cancelled" in result.stdout
    assert called is False
    assert session.closed is True
