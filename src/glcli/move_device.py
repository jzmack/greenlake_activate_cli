import requests
import json
import logging
import re

from glcli.query_inventory import query_inventory

logger = logging.getLogger(__name__)
UPDATE_INVENTORY_URL = "https://activate.arubanetworks.com/api/ext/inventory.json?action=update"
REQUEST_TIMEOUT = 30
MAC_PATTERN = re.compile(r"^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$", re.IGNORECASE)

def move_device(
    session: requests.Session,
    mac_addresses: list[str],
    destination_folder: str,
) -> str:
    """Move MAC addresses to a folder name or numeric folder ID."""
    if not mac_addresses:
        raise ValueError("At least one MAC address is required")
    destination_folder = destination_folder.strip()
    if not destination_folder:
        raise ValueError("A destination folder is required")

    destination_key = "folderId" if destination_folder.isdigit() else "folderName"
    payload = {
        "devices": [
            {"mac": mac, destination_key: destination_folder}
            for mac in mac_addresses
        ]
    }
    raw_data = f"json={json.dumps(payload)}"
    logger.debug("Move request: %s", raw_data)
    response = session.post(UPDATE_INVENTORY_URL, data=raw_data, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        logger.error("Move failed with status code: %s", response.status_code)
        raise RuntimeError("Inventory move failed")

    logger.info("Moved %d device(s) to %s", len(mac_addresses), destination_folder)
    return response.text


def resolve_move_macs(
    session: requests.Session,
    identifier_type: str,
    identifiers: list[str],
) -> tuple[list[str], list[str]]:
    """Resolve valid serial or MAC identifiers to canonical MAC addresses."""
    if identifier_type not in {"serial", "mac"}:
        raise ValueError(f"Unsupported move identifier type: {identifier_type}")

    response_text, missing = query_inventory(session, identifier_type, identifiers)
    try:
        response = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Activate returned invalid inventory JSON") from exc

    resolved: list[str] = []
    unresolved = list(missing)
    for device in response.get("devices", []):
        if not isinstance(device, dict):
            continue
        mac = str(device.get("mac") or "").strip().upper()
        if not MAC_PATTERN.fullmatch(mac):
            identifier = device.get("serialNumber") if identifier_type == "serial" else device.get("mac")
            if identifier:
                unresolved.append(str(identifier))
            continue
        resolved.append(mac)

    return list(dict.fromkeys(resolved)), list(dict.fromkeys(unresolved))
