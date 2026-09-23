from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

def display_inventory_sn(extracted_data:list[dict]):
    """Function to display output on the CLI when querying by SN"""

    console = Console()
    table = Table(
        "Serial",
        "MAC Address",
        "Status",
        "Folder",
        "Folder ID",
        title=f"Query Results - {len(extracted_data)} Device(s)",
        header_style="wheat1",
        box=box.ROUNDED,
    )

    for device in extracted_data:
        table.add_row(
            device['serial'],
            Text(device['mac']), # render as Text so it doesn't display emojis
            device['status'],
            device['folder'],
            device['folderId']
        )

    console.print(table)
