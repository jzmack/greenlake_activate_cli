import logging
from pathlib import Path

import typer
from glcli.activate_login import create_activate_session, load_credentials
from glcli.data_parsing import parse_inventory_response
from glcli.query_inventory import query_inventory, read_identifiers_from_file
from glcli.display_data import display_inventory_sn
from rich.logging import RichHandler

logger = logging.getLogger(__name__)
app = typer.Typer(help="Interact with HPE GreenLake Activate via CLI.")
query_app = typer.Typer(help="Query Activate inventory.")
app.add_typer(query_app, name="query")

def setup_logging(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s" if verbose else "%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_path=verbose)],
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def _query(identifier_type: str, identifiers: list[str], file: Path | None = None) -> None:
    if file is not None:
        identifiers = read_identifiers_from_file(file, identifier_type)

    identifiers = [identifier.strip().upper() for identifier in identifiers if identifier.strip()]
    if not identifiers:
        raise typer.BadParameter("At least one identifier is required")

    identifiers = list(dict.fromkeys(identifiers))
    credential = load_credentials()
    try:
        session = create_activate_session(credential)
        query_result, missing = query_inventory(session, identifier_type, identifiers)
    finally:
        if "session" in locals():
            session.close()

    extracted_data = parse_inventory_response(query_result)

    if missing:
        print(f"Not found: ({len(missing)}): {', '.join(missing)}")

    display_inventory_sn(extracted_data)

    if not extracted_data:
        raise typer.Exit(code=1)
    if missing:
        raise typer.Exit(code=2)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debugging output to console."),
) -> None:
    setup_logging(verbose)


@query_app.command("serial")
def query_serial(
    serials: list[str] | None = typer.Argument(None, metavar="SERIAL"),
    file: Path | None = typer.Option(None, "--file", "-f", help="CSV or text file containing serial numbers."),
) -> None:
    _query("serial", serials or [], file)


@query_app.command("mac")
def query_mac(
    macs: list[str] | None = typer.Argument(None, metavar="MAC"),
    file: Path | None = typer.Option(None, "--file", "-f", help="CSV or text file containing MAC addresses."),
) -> None:
    _query("mac", macs or [], file)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
