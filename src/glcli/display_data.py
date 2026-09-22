from rich import box
from rich.console import Console
from rich.table import Table

def display_inventory_sn(extracted_data:list[dict]):
    """Function to display output on the CLI when querying by SN"""

    console = Console()
    table = Table(
        "Serial",
        "MAC Address",
        "Status",
        "Folder",
        "Folder ID",
        title="Query Results",
        header_style="wheat1",
        box=box.ROUNDED
    )

    for device in extracted_data:
        table.add_row(
            device['serial'],
            device['mac'],
            device['status'],
            device['folder'],
            device['folderId']
        )

    console.print(table)
