from rich import print

def display_inventory_sn(extracted_data:list[dict]):
    """Function to display output on the CLI when querying by SN"""

    indent = " " * 5
    for device in extracted_data:
        print()
        print(f"[yellow]Serial[/yellow]: [white]{device['serial']}[/white]")
        print(f"{indent}[yellow]MAC Address[/yellow]: [white]{device['mac']}[/white]")
        print(f"{indent}[yellow]Status[/yellow]: [white]{device['status']}[/white]")
        print(f"{indent}[yellow]Folder[/yellow]: [white]{device['folder']}[/white]")
        print(f"{indent}[yellow]Folder ID[/yellow]: [white]{device['folderId']}[/white]")
