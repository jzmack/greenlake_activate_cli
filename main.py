from activate_login import create_activate_session, load_credentials

def main():
    credentials = load_credentials()
    create_activate_session(credentials)

if __name__ == "__main__":
    main()
