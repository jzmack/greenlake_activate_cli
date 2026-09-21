import json

import pytest

from glcli.query_folder import Folder, list_folders, resolve_folder_ids


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


def test_list_folders_parses_folder_records():
    session = FakeSession(FakeResponse({"folders": [{"id": "5297450", "folderName": "SiteA-South"}]}))

    folders = list_folders(session)

    assert folders == [Folder("5297450", "SiteA-South")]
    assert session.calls[0][1] == ""


def test_resolve_folder_names_case_insensitively_and_deduplicates():
    session = FakeSession(FakeResponse({
        "folders": [
            {"id": "1", "folderName": "SiteA-South"},
            {"id": "2", "folderName": "SiteB-North"},
        ]
    }))

    assert resolve_folder_ids(session, ["sitea-south", "2", "SiteA-South"]) == ["1", "2"]


def test_numeric_folder_ids_skip_folder_lookup():
    session = FakeSession(FakeResponse({"folders": []}))

    assert resolve_folder_ids(session, ["1", "2"]) == ["1", "2"]
    assert session.calls == []


def test_resolve_folder_name_reports_missing_folder():
    session = FakeSession(FakeResponse({"folders": []}))

    with pytest.raises(ValueError, match="not found"):
        resolve_folder_ids(session, ["Unknown"])


def test_resolve_folder_name_reports_ambiguous_folder():
    session = FakeSession(FakeResponse({
        "folders": [
            {"id": "1", "folderName": "SiteA"},
            {"id": "2", "folderName": "sitea"},
        ]
    }))

    with pytest.raises(ValueError, match="ambiguous"):
        resolve_folder_ids(session, ["SiteA"])
