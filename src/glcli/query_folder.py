import requests
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)
FOLDER_URL = "https://activate.arubanetworks.com/api/ext/folder.json?action=query"
REQUEST_TIMEOUT = 30


@dataclass(frozen=True)
class Folder:
    folder_id: str
    name: str


def list_folders(session: requests.Session) -> list[Folder]:
    """Return all folders visible to the authenticated Activate session."""
    response = session.post(FOLDER_URL, data="", timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        logger.error("Folder query failure code: %s", response.status_code)
        raise RuntimeError("Folder query failed.")

    try:
        payload = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Activate returned invalid folder JSON") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("folders"), list):
        raise RuntimeError("Activate returned an invalid folder response")

    folders = []
    for item in payload["folders"]:
        if not isinstance(item, dict) or not item.get("id") or not item.get("folderName"):
            continue
        folders.append(Folder(str(item["id"]), str(item["folderName"])))

    logger.debug("Read %d folder(s) from Activate", len(folders))
    return folders


def resolve_folder_ids(session: requests.Session, values: list[str]) -> list[str]:
    """Resolve folder IDs and exact case-insensitive folder names."""
    if all(value.isdigit() for value in values):
        return list(dict.fromkeys(values))

    folders = list_folders(session)
    by_name: dict[str, list[Folder]] = {}
    for folder in folders:
        by_name.setdefault(folder.name.casefold(), []).append(folder)

    resolved: list[str] = []
    missing: list[str] = []
    ambiguous: dict[str, list[str]] = {}
    for value in values:
        if value.isdigit():
            resolved.append(value)
            continue

        matches = by_name.get(value.casefold(), [])
        if not matches:
            missing.append(value)
        elif len(matches) > 1:
            ambiguous[value] = [folder.folder_id for folder in matches]
        else:
            resolved.append(matches[0].folder_id)

    if missing:
        raise ValueError(f"Folder(s) not found: {', '.join(missing)}")
    if ambiguous:
        details = "; ".join(f"{name}: {', '.join(ids)}" for name, ids in ambiguous.items())
        raise ValueError(f"Folder name(s) are ambiguous: {details}")

    return list(dict.fromkeys(resolved))
