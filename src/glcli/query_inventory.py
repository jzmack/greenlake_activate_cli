import requests
import json
import logging
import csv
from pathlib import Path

logger = logging.getLogger(__name__)

def query_by_serial(session: requests.Session, serial_numbers: list[str]):
    """Function to query GreenLake Activate inventory given a list of Serial Numbers"""
    inventory_url = "https://activate.arubanetworks.com/api/ext/inventory.json?action=query"
    payload = {
       "serialNumbers":serial_numbers
    }
    raw_data = f"json={json.dumps(payload)}"
    logging.debug("Query string: %s", raw_data)

    logging.debug("Attempting to query activate inventory: %s", inventory_url)
    response = session.post(inventory_url, data=raw_data)

    if response.status_code != 200:
        logging.error("Query failure code: %s", response.status_code)
        raise RuntimeError("Query failed.")

    json_response:dict = json.loads(response.text)

    found = {d["serialNumber"].upper() for d in json_response.get("devices", [])}
    missing = [s for s in serial_numbers if s.upper() not in found]

    if missing:
        logger.warning("Not found in Activate inventory: %s", ", ".join(missing))

    logging.info("Query succeeded!")
    logging.debug("Full query response:\n%s", response.text )

    return response.text, missing

def read_serials_from_file(path: Path) -> list[str]:
    """Read serial numbers from a CSV or newline-delimited text file."""
    SERIAL_COLUMNS = {"serial", "serialnumber", "serial_number", "serial number", "sn"}
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))

    if not rows:
        raise ValueError(f"File is empty: {path}")

    header = [c.strip().lower() for c in rows[0]]
    col = next((i for i, c in enumerate(header) if c in SERIAL_COLUMNS), None)

    if col is None:
        logger.debug("No serial header found in %s; reading first column", path)
        col = 0
        data = rows
    else:
        logger.debug("Using column '%s' (index %d)", header[col], col)
        data = rows[1:]

    serials = [
        row[col].strip().upper()
        for row in data
        if row and len(row) > col and row[col].strip()
    ]

    logger.info("Read %d serial(s) from %s", len(serials), path)
    return serials


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
