import json

import pytest

from glcli.query_inventory import query_inventory
from glcli.query_inventory import read_identifiers_from_file


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


def test_folder_query_uses_folders_payload():
    session = FakeSession({"devices": [{"serialNumber": "SN1"}]})

    response, missing = query_inventory(session, "folder", ["5297450", "5389522"])

    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "folders": ["5297450", "5389522"]
    }
    assert json.loads(response)["devices"][0]["serialNumber"] == "SN1"
    assert missing == []


def test_invalid_inventory_json_is_reported():
    session = FakeSession({"devices": []})
    session.post = lambda url, data, timeout: type("Response", (), {"status_code": 200, "text": "bad"})()

    with pytest.raises(RuntimeError, match="invalid JSON"):
        query_inventory(session, "serial", ["SN1"])


def test_mac_file_reader_skips_mac_header(tmp_path):
    mac_file = tmp_path / "macs.csv"
    mac_file.write_text("mac_address\naa:bb:cc:00:11:22\n")

    assert read_identifiers_from_file(mac_file, "mac") == ["AA:BB:CC:00:11:22"]
