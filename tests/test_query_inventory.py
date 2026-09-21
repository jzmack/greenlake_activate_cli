import json

import pytest

from glcli.query_inventory import query_inventory


class FakeResponse:
    status_code = 200

    def __init__(self, body):
        self.text = json.dumps(body)


class FakeSession:
    def __init__(self, body):
        self.body = body
        self.calls = []

    def post(self, url, data, timeout):
        self.calls.append((url, data, timeout))
        return FakeResponse(self.body)


def test_serial_query_uses_serial_numbers_payload():
    session = FakeSession({"devices": [{"serialNumber": "SN1"}]})

    response, missing = query_inventory(session, "serial", ["SN1", "SN2"])

    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "serialNumbers": ["SN1", "SN2"]
    }
    assert json.loads(response)["devices"][0]["serialNumber"] == "SN1"
    assert missing == ["SN2"]


def test_mac_query_uses_devices_payload_and_matches_case_insensitively():
    session = FakeSession({"devices": [{"mac": "AA:BB:CC:00:11:22"}]})

    _, missing = query_inventory(session, "mac", ["aa:bb:cc:00:11:22", "DD:EE:FF:33:44:55"])

    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "devices": ["aa:bb:cc:00:11:22", "DD:EE:FF:33:44:55"]
    }
    assert missing == ["DD:EE:FF:33:44:55"]


def test_invalid_inventory_json_is_reported():
    session = FakeSession({"devices": []})
    session.post = lambda url, data, timeout: type("Response", (), {"status_code": 200, "text": "bad"})()

    with pytest.raises(RuntimeError, match="invalid JSON"):
        query_inventory(session, "serial", ["SN1"])
