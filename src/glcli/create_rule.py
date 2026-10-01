import json
import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)
CREATE_RULE_URL = "https://activate.arubanetworks.com/api/ext/rule.json?action=update"
REQUEST_TIMEOUT = 30


@dataclass(frozen=True)
class CreatedProvisionRule:
    rule_id: str
    name: str


def create_provision_rule(
    session: requests.Session,
    rule_name: str,
    folder_id: str,
    provision_type: str,
    controller_ip: str,
    ap_group: str,
) -> CreatedProvisionRule:
    """Create one Activate provisioning rule and return its assigned ID."""
    values = (rule_name, folder_id, provision_type, controller_ip, ap_group)
    if any(not value.strip() for value in values):
        raise ValueError("All provisioning rule fields are required")

    payload = {
        "rules": [{
            "ruleName": rule_name.strip(),
            "parentFolderId": folder_id.strip(),
            "ruleType": "provision",
            "provisionType": provision_type,
            "controller": controller_ip.strip(),
            "apGroup": ap_group.strip(),
        }]
    }

    raw_payload = f"json={json.dumps(payload)}"

    response = session.post(CREATE_RULE_URL, data=raw_payload, timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        logger.error("Non 200 code returned from rule API: %s", response.status_code)
        raise RuntimeError("Failed to create provisioning rule")

    try:
        response_data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Activate returned invalid rule JSON") from exc

    if not isinstance(response_data, dict):
        raise RuntimeError("Activate returned an invalid rule response")

    message = response_data.get("message")
    if isinstance(message, dict) and message.get("code") is not None and str(message["code"]) != "0":
        raise RuntimeError(message.get("text") or "Activate rejected the provisioning rule")

    rules = response_data.get("rules")
    if not isinstance(rules, list) or not rules or not isinstance(rules[0], dict):
        raise RuntimeError("Activate returned an invalid rule creation response")

    created_rule = rules[0]
    rule_id = created_rule.get("ruleId")
    returned_name = created_rule.get("ruleName")
    if not rule_id or not returned_name:
        raise RuntimeError("Activate response is missing the created rule ID or name")

    result = CreatedProvisionRule(str(rule_id), str(returned_name))
    logger.info("Created provisioning rule '%s' with ID %s", result.name, result.rule_id)
    return result
