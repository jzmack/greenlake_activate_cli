import argparse

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Interact with HPE GreenLake Activate via CLI."
    )
    parser.add_argument(
        "serial_numbers",
        nargs="+",
        metavar="SERIAL",
        help="One or more serial numbers to look up (space separated)."
    )
    return parser.parse_args()
