from io import StringIO

from rich.console import Console

from glcli.display_data import display_rules


def test_display_rules_includes_rule_fields_and_handles_missing_values():
    output = StringIO()
    console = Console(file=output, width=160)

    display_rules(
        [{
            "ruleId": "63111165",
            "ruleName": "PUH provision",
            "parentFolderId": "63111131",
            "ruleType": "provision",
            "provisionType": "iap_to_cap",
            "persistControllerIp": "true",
            "controller": "10.49.4.11",
            "apGroup": None,
        }],
        console,
    )

    rendered = output.getvalue()
    for expected in ("63111165", "PUH provision", "63111131", "iap_to_cap", "10.49.4.11", "-"):
        assert expected in rendered


def test_display_rules_displays_empty_state():
    output = StringIO()

    display_rules([], Console(file=output, width=120))

    assert "0 Rule(s)" in output.getvalue()
