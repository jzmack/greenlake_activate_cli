import json
import logging

import requests


logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 30
RULE_URL = "https://activate.arubanetworks.com/api/ext/rule.json?action=query"


def query_rule(session: requests.Session, folder_id: str) -> list[dict]:
    """Query provisioning rules for one Activate folder."""
    folder_id = folder_id.strip()
    if not folder_id:
        raise ValueError("A folder ID is required")

    payload = {"folders": [folder_id]}
    raw_payload = f"json={json.dumps(payload)}"
    logger.debug("Rule query payload: %s", raw_payload)

    logger.debug("Attempting to query rule: %s", RULE_URL)
    response = session.post(RULE_URL, data=raw_payload, timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        logger.error("Query failed. Status code: %s", response.status_code)
        raise RuntimeError("Rule query failed.")

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Activate returned invalid rule JSON") from exc

    if not isinstance(response_data, dict) or not isinstance(response_data.get("rules"), list):
        raise RuntimeError("Activate returned an invalid rule response")

    rules = [rule for rule in response_data["rules"] if isinstance(rule, dict)]
    logger.debug("Received %d rule(s)", len(rules))
    return rules
