import requests
import json

def query_by_serial(session: requests.Session, serial_numbers: list[str]):
    """Function to query GreenLake Activate inventory given a list of Serial Numbers"""
    inventory_url = "https://activate.arubanetworks.com/api/ext/inventory.json?action=query"
    payload = {
       "serialNumbers":serial_numbers
    }
    raw_data = f"json={json.dumps(payload)}"
    response = session.post(inventory_url, data=raw_data)

    if response.status_code != 200:
        response.raise_for_status()

    # print(response.text)

    return response.text
