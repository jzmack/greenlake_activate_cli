from activate_login import create_activate_session, load_credentials
from query_inventory import query_by_serial
from cli_args import parse_cli_args

def main():
    args = parse_cli_args()
    credentials = load_credentials()

    try:
        session = create_activate_session(credentials)
        query_by_serial(session, args.serial_numbers)
    finally:
        session.close()

if __name__ == "__main__":
    main()
