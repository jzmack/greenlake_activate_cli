import json
import logging

logger = logging.getLogger(__name__)

def parse_inventory_response(response:str) -> list[dict]:
    """Function to extract the data that I want to get from Activate."""

    try:
        json_obj = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("Inventory response is not valid JSON") from exc

    if not isinstance(json_obj, dict):
        raise ValueError("Inventory response must be a JSON object")

    extracted_data: list[dict] = [] # each device is a dictionary
    devices = json_obj.get("devices")

    if isinstance(devices, list):
       for device in devices:
          if not isinstance(device, dict):
              continue

          serial = device.get("serialNumber")
          mac = device.get("mac")
          status = device.get("status")
          additional_data = device.get("additionalData")
          if not isinstance(additional_data, dict):
              additional_data = {}
          folder = additional_data.get("folder")
          folder_id = additional_data.get("folderId")

          device_dict = {
              "serial":serial,
              "mac":mac,
              "status":status,
              "folder":folder,
              "folderId":folder_id,

          }
          extracted_data.append(device_dict)

    logger.debug("Extracted data:\n%s", extracted_data)
    return extracted_data
