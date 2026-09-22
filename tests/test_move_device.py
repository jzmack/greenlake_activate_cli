import json

import pytest

from glcli.move_device import move_device, resolve_move_macs


class FakeResponse:
    def __init__(self, body, status_code=200):
        self.text = json.dumps(body) if not isinstance(body, str) else body
        self.status_code = status_code


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def post(self, url, data, timeout):
        self.calls.append((url, data, timeout))
        return next(self.responses)


def test_move_uses_folder_name_payload_and_session():
    session = FakeSession([FakeResponse({"message": {"code": 0}})])

    move_device(session, ["AA:BB:CC:DD:EE:FF"], "Northwest")

    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "devices": [{"mac": "AA:BB:CC:DD:EE:FF", "folderName": "Northwest"}]
    }


def test_move_uses_folder_id_payload_for_numeric_destination():
    session = FakeSession([FakeResponse({"message": {"code": 0}})])

    move_device(session, ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"], "5297450")

    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "devices": [
            {"mac": "AA:BB:CC:DD:EE:FF", "folderId": "5297450"},
            {"mac": "11:22:33:44:55:66", "folderId": "5297450"},
        ]
    }


def test_resolve_serials_to_macs():
    session = FakeSession([
        FakeResponse({"devices": [{"serialNumber": "SN1", "mac": "AA:BB:CC:DD:EE:FF"}]}),
    ])

    macs, missing = resolve_move_macs(session, "serial", ["SN1"])

    assert macs == ["AA:BB:CC:DD:EE:FF"]
    assert missing == []


def test_move_rejects_failed_update():
    session = FakeSession([FakeResponse({"error": "failed"}, status_code=500)])

    with pytest.raises(RuntimeError, match="move failed"):
        move_device(session, ["AA:BB:CC:DD:EE:FF"], "Northwest")
