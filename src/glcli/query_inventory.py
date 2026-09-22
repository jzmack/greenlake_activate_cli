import requests
import json
import logging
import csv
from pathlib import Path

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 30

def query_inventory(session: requests.Session, identifier_type: str, identifiers: list[str]):
    """Query GreenLake Activate inventory by serial number or MAC address."""
    inventory_url = "https://activate.arubanetworks.com/api/ext/inventory.json?action=query"
    if identifier_type == "serial":
        payload = {"serialNumbers": identifiers}
        response_key = "serialNumber"
    elif identifier_type == "mac":
        payload = {"devices": identifiers}
        response_key = "mac"
    elif identifier_type == "folder":
        payload = {"folders": identifiers}
        response_key = None
    else:
        raise ValueError(f"Unsupported inventory query type: {identifier_type}")

    raw_data = f"json={json.dumps(payload)}"
    logger.debug("Query string: %s", raw_data)

    logger.debug("Attempting to query activate inventory: %s", inventory_url)
    response = session.post(inventory_url, data=raw_data, timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        logger.error("Query failure code: %s", response.status_code)
        raise RuntimeError("Query failed.")

    try:
        json_response = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Activate returned invalid JSON") from exc

    if not isinstance(json_response, dict) or not isinstance(json_response.get("devices", []), list):
        raise RuntimeError("Activate returned an invalid inventory response")

    if response_key is None:
        missing = []
    else:
        found = {
            str(device[response_key]).upper()
            for device in json_response.get("devices", [])
            if isinstance(device, dict) and device.get(response_key)
        }
        missing = [identifier for identifier in identifiers if identifier.upper() not in found]

    if missing:
        logger.warning("Not found in Activate inventory: %s", ", ".join(missing))

    logger.debug("Query succeeded!")
    logger.debug("Full query response:\n%s", response.text)

    return response.text, missing


def query_by_serial(session: requests.Session, serial_numbers: list[str]):
    """Query GreenLake Activate inventory by serial number."""
    return query_inventory(session, "serial", serial_numbers)


def query_by_mac(session: requests.Session, mac_addresses: list[str]):
    """Query GreenLake Activate inventory by MAC address."""
    return query_inventory(session, "mac", mac_addresses)


def query_by_folder(session: requests.Session, folder_ids: list[str]):
    """Query GreenLake Activate inventory by folder ID."""
    return query_inventory(session, "folder", folder_ids)

def read_identifiers_from_file(path: Path, identifier_type: str = "serial") -> list[str]:
    """Read serial numbers or MAC addresses from a CSV or newline-delimited file."""
    if identifier_type not in {"serial", "mac"}:
        raise ValueError(f"Unsupported identifier type: {identifier_type}")

    columns_by_type = {
        "serial": {"serial", "serialnumber", "serial_number", "serial number", "sn"},
        "mac": {"mac", "macaddress", "mac_address", "mac address", "ethernet address"},
    }
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))

    if not rows:
        raise ValueError(f"File is empty: {path}")

    header = [c.strip().lower() for c in rows[0]]
    col = next((i for i, c in enumerate(header) if c in columns_by_type[identifier_type]), None)

    if col is None:
        logger.debug("No serial header found in %s; reading first column", path)
        col = 0
        data = rows
    else:
        logger.debug("Using column '%s' (index %d)", header[col], col)
        data = rows[1:]

    identifiers = [
        row[col].strip().upper()
        for row in data
        if row and len(row) > col and row[col].strip()
    ]

    logger.info("Read %d %s(s) from %s", len(identifiers), identifier_type, path)
    return identifiers


def read_serials_from_file(path: Path) -> list[str]:
    """Read serial numbers from a CSV or newline-delimited text file."""
    return read_identifiers_from_file(path, "serial")


def get_serials(args) -> list[str]:
    """Resolve serial numbers from either --file or the positional args."""
    if args.file:
        serials = read_serials_from_file(args.file)
    else:
        serials = args.serials

    serials = [s.strip().upper() for s in serials if s.strip()]

    if not serials:
        raise ValueError("No serial numbers provided.")

    deduped = list(dict.fromkeys(serials))
    if len(deduped) != len(serials):
        logger.warning("Removed %d duplicate serial(s)", len(serials) - len(deduped))

    return deduped
