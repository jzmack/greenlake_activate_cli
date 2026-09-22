import requests
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)
CREATE_FOLDER_URL = "https://activate.arubanetworks.com/api/ext/folder.json?action=create"
REQUEST_TIMEOUT = 30


@dataclass(frozen=True)
class CreatedFolder:
    folder_id: str
    name: str


def create_folder(session: requests.Session, folder_name: str) -> CreatedFolder:
    """Create an Activate folder and return its assigned ID and name."""
    folder_name = folder_name.strip()
    if not folder_name:
        raise ValueError("A folder name is required")

    payload = {"folder": {"folderName": folder_name}}
    raw_data = f"json={json.dumps(payload)}"
    response = session.post(CREATE_FOLDER_URL, data=raw_data, timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        logger.error("Non 200 code returned from folder API: %s", response.status_code)
        raise RuntimeError("Failed to create folder.")

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Activate returned invalid folder JSON") from exc

    folder = response_data.get("folder") if isinstance(response_data, dict) else None
    if not isinstance(folder, dict) or not folder.get("folderId") or not folder.get("folderName"):
        raise RuntimeError("Activate returned an invalid folder creation response")

    created_folder = CreatedFolder(str(folder["folderId"]), str(folder["folderName"]))
    logger.debug("Created folder '%s' with ID %s", created_folder.name, created_folder.folder_id)
    return created_folder
