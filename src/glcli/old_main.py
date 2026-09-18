from glcli.activate_login import create_activate_session,load_credentials
from glcli.query_inventory import query_by_serial
from glcli.data_parsing import parse_inventory_response
from glcli.display_data import display_inventory_sn
from glcli.cli import parse_cli_args

def main():
    args = parse_cli_args()
    credentials = load_credentials()

    try:
        session = create_activate_session(credentials)
        query_response = query_by_serial(session, args.serial_numbers)
        extracted_data = parse_inventory_response(query_response)
        display_inventory_sn(extracted_data)
    finally:
        session.close()

if __name__ == "__main__":
    main()
