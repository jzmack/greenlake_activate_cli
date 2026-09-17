def display_inventory_sn(extracted_data:list[dict]):
    """Function to display output on the CLI when querying by SN"""

    indent = " " * 5
    for device in extracted_data:
        print()
        print(f"{'Serial:'} {device['serial']}")
        print(f"{indent}{'MAC Address:'} {device['mac']}")
        print(f"{indent}{'Status:'} {device['status']}")
        print(f"{indent}{'Folder:'} {device['folder']}")
        print(f"{indent}{'Folder ID:'} {device['folderId']}")
