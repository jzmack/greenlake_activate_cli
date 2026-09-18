import requests
import json
import logging

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

    logging.info("Query succeeded:\n%s", response.text)

    return response.text, missing
