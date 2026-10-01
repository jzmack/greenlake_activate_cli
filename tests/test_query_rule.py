import json

import pytest

from glcli.query_rule import RULE_URL, query_rule


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


def test_rule_query_sends_single_folder_id_as_array():
    rules = [{"ruleId": "63111165", "ruleName": "PUH provision"}]
    session = FakeSession(FakeResponse({"rules": rules}))

    assert query_rule(session, " 63111131 ") == rules
    assert session.calls[0][0] == RULE_URL
    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "folders": ["63111131"]
    }


def test_rule_query_accepts_empty_rules():
    assert query_rule(FakeSession(FakeResponse({"rules": []})), "63111131") == []


def test_rule_query_rejects_invalid_json():
    with pytest.raises(RuntimeError, match="invalid rule JSON"):
        query_rule(FakeSession(FakeResponse("not-json")), "63111131")


def test_rule_query_rejects_non_200_response():
    with pytest.raises(RuntimeError, match="Rule query failed"):
        query_rule(FakeSession(FakeResponse({}, status_code=500)), "63111131")


def test_rule_query_rejects_missing_rules_list():
    with pytest.raises(RuntimeError, match="invalid rule response"):
        query_rule(FakeSession(FakeResponse({"devices": []})), "63111131")
