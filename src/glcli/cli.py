import argparse
import sys
import logging

from glcli.activate_login import create_activate_session, load_credentials
from glcli.data_parsing import parse_inventory_response
from glcli.query_inventory import query_by_serial
from glcli.display_data import display_inventory_sn
from rich.logging import RichHandler

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s" if verbose else "%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_path=verbose)],
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def parse_cli_args(argv=None):
    """Used to create arguments that can be passed during exectuion."""

    parser = argparse.ArgumentParser(
        prog="glcli",
        description="Interact with HPE GreenLake Activate via CLI."
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debugging output to console."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # glcli query
    p_query = subparsers.add_parser("query", help="Query Inventory.")
    p_query.add_argument(
        "serials",
        nargs="+",
        metavar="SERIAL",
        help="Serial numbers (space separated) or 'all' to query everything."
    )
    p_query.set_defaults(func=cmd_query)

    return parser.parse_args(argv)

def cmd_query(session, args) -> int:
    query_result, missing = query_by_serial(session, args.serials)
    extracted_data = parse_inventory_response(query_result)

    if missing:
        print(f"Not found: ({len(missing)}): {', '.join(missing)}")

    display_inventory_sn(extracted_data)

    if not extracted_data:
        return 1
    return 2 if missing else 0

def main(argv=None):
    args = parse_cli_args(argv)

    setup_logging(args.verbose)
    logger.debug("Parsed arguments: %s", args)

    token = load_credentials()
    session = create_activate_session(token)
    return args.func(session, args)

if __name__ == "__main__":
    sys.exit(main())
