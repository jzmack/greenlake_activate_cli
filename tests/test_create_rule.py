import json

import pytest

from glcli.create_rule import (
    CREATE_RULE_URL,
    CreatedProvisionRule,
    create_provision_rule,
)


class FakeResponse:
    def __init__(self, body, status_code=200):
        self.text = json.dumps(body) if not isinstance(body, str) else body
        self.status_code = status_code


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, data, timeout):
        self.calls.append((url, data, timeout))
        return self.response


@pytest.mark.parametrize(
    ("choice", "expected_api_type"),
    [("iap_to_cap", "iap_to_cap"), ("iap_to_rap", "iap_to_rap")],
)
def test_create_rule_sends_expected_payload(choice, expected_api_type):
    session = FakeSession(FakeResponse({
        "message": {"code": "0", "text": "1 rules updated."},
        "rules": [{"ruleId": "70081128", "ruleName": "test_rule"}],
    }))

    result = create_provision_rule(
        session, "test_rule", "63061537", choice, "10.103.6.18", "indoor"
    )

    assert result == CreatedProvisionRule("70081128", "test_rule")
    assert session.calls[0][0] == CREATE_RULE_URL
    assert session.calls[0][2] == 30
    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "rules": [{
            "ruleName": "test_rule",
            "parentFolderId": "63061537",
            "ruleType": "provision",
            "provisionType": expected_api_type,
            "controller": "10.103.6.18",
            "apGroup": "indoor",
        }]
    }


def test_create_rule_rejects_non_200_response():
    session = FakeSession(FakeResponse({}, status_code=500))

    with pytest.raises(RuntimeError, match="Failed to create provisioning rule"):
        create_provision_rule(session, "rule", "1", "iap_to_cap", "10.0.0.1", "ap")


def test_create_rule_rejects_invalid_json():
    session = FakeSession(FakeResponse("not-json"))

    with pytest.raises(RuntimeError, match="invalid rule JSON"):
        create_provision_rule(session, "rule", "1", "iap_to_cap", "10.0.0.1", "ap")


def test_create_rule_rejects_unsuccessful_api_message():
    session = FakeSession(FakeResponse({
        "message": {"code": "4", "text": "Invalid controller"},
        "rules": [],
    }))

    with pytest.raises(RuntimeError, match="Invalid controller"):
        create_provision_rule(session, "rule", "1", "iap_to_cap", "bad", "ap")
