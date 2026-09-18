import argparse
import sys

from glcli.activate_login import create_activate_session, load_credentials
from glcli.data_parsing import parse_inventory_response
from glcli.query_inventory import query_by_serial
from glcli.display_data import display_inventory_sn

def parse_cli_args(argv=None):
    """Used to create arguments that can be passed during exectuion."""

    parser = argparse.ArgumentParser(
        prog="glcli",
        description="Interact with HPE GreenLake Activate via CLI."
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
    query_result = query_by_serial(session, args.serials)
    extracted_data = parse_inventory_response(query_result)
    display_inventory_sn(extracted_data)
    return 0

def main(argv=None):
    args = parse_cli_args(argv)
    token = load_credentials()
    session = create_activate_session(token)
    return args.func(session, args)

if __name__ == "__main__":
    sys.exit(main())
