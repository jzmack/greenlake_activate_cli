import json

import pytest

from glcli.create_folder import CreatedFolder, create_folder


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


def test_create_folder_sends_expected_payload_and_parses_response():
    session = FakeSession(FakeResponse({
        "folder": {"folderId": "69832536", "folderName": "Jake_test2"}
    }))

    result = create_folder(session, "  Jake_test2  ")

    assert result == CreatedFolder("69832536", "Jake_test2")
    assert json.loads(session.calls[0][1].removeprefix("json=")) == {
        "folder": {"folderName": "Jake_test2"}
    }


def test_create_folder_rejects_empty_name():
    with pytest.raises(ValueError, match="folder name is required"):
        create_folder(FakeSession(FakeResponse({})), "  ")


def test_create_folder_rejects_invalid_json():
    session = FakeSession(FakeResponse("not-json"))

    with pytest.raises(RuntimeError, match="invalid folder JSON"):
        create_folder(session, "Northwest")


def test_create_folder_rejects_failed_request():
    session = FakeSession(FakeResponse({}, status_code=500))

    with pytest.raises(RuntimeError, match="Failed to create folder"):
        create_folder(session, "Northwest")
