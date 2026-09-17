import requests
import os
from dotenv import load_dotenv

def load_credentials():
    """Load credentials from .env file"""
    load_dotenv()
    return os.getenv("CREDENTIAL_1")

def create_activate_session(credential_1:str):
    """Login and save session cookie"""
    login_url = "https://activate.arubanetworks.com/LOGIN"
    login_data = {
        'credential_0': "username",
        'credential_1': credential_1
    }
    session = requests.session()
    response = session.post(login_url, data=login_data)
    print(f"Login Status Code: {response.status_code}")
    print(f"Login response: {response.text}")
    return session
