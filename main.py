from activate_login import create_activate_session, load_credentials
from query_inventory import query_by_serial

def main():
    credentials = load_credentials()
    session = create_activate_session(credentials)
    query_by_serial(session, ["PHWJKSM0MK"])

if __name__ == "__main__":
    main()
