import json

def parse_inventory_response(response:str) -> list[dict]:
    json_obj = json.loads(response)
    extracted_data: list[dict] = [] # each device is a dictionary
    devices = json_obj.get("devices")

    if devices:
       for device in devices:
          serial = device.get("serialNumber")
          mac = device.get("mac")
          status = device.get("status")
          folder = device.get("additionalData").get("folder")
          folder_id = device.get("additionalData").get("folderId")
          device_dict = {
              "serial":serial,
              "mac":mac,
              "status":status,
              "folder":folder,
              "folderId":folder_id,

          }
          extracted_data.append(device_dict)
    return extracted_data
