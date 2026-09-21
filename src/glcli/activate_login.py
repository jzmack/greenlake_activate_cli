import requests
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 30

def load_credentials() -> str | None:
    """Load credentials from .env file"""
    load_dotenv()
    return os.getenv("CREDENTIAL_1")

def create_activate_session(credential_1:str) -> requests.Session:
    """Login and return session."""
    if not credential_1:
        raise RuntimeError("CREDENTIAL_1 is not configured")

    login_url = "https://activate.arubanetworks.com/LOGIN"
    login_data = {
        'credential_0': "username",
        'credential_1': credential_1
    }
    logger.debug("Attempting to authenticate to: %s", login_url)
    session = requests.session()
    response = session.post(login_url, data=login_data, timeout=REQUEST_TIMEOUT)

    logger.debug("Login status code: %s", response.status_code)
    if response.status_code != 200:
        logger.error("Login failed: %s", response.text)
        raise RuntimeError("Activate login failed")

    logger.info("Authenticated to Activate")
    logger.debug("Full login response: %s", response.text)

    return session
