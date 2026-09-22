import os
import logging
from pathlib import Path

import requests
from dotenv import dotenv_values

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 30
ENVIRONMENT_VARIABLE = "CREDENTIAL_1"


def user_config_path() -> Path:
    """Return the user-level configuration path for the current platform."""
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "greenlake-activate-cli" / ".env"
    return Path.home() / ".config" / "greenlake-activate-cli" / ".env"


def credential_config_paths() -> tuple[Path, Path]:
    """Return user-level and project-local credential file paths."""
    return user_config_path(), Path.cwd() / ".env"


def save_user_credential(credential: str) -> Path:
    """Save a credential in the user-level dotenv configuration file."""
    credential = credential.strip()
    if not credential:
        raise ValueError("CREDENTIAL_1 cannot be empty")

    config_path = user_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.parent.chmod(0o700)
    config_path.write_text(f"{ENVIRONMENT_VARIABLE}={credential}\n", encoding="utf-8")
    config_path.chmod(0o600)
    return config_path


def load_credentials() -> str:
    """Load credentials using environment, user config, then local config."""
    credential = os.environ.get(ENVIRONMENT_VARIABLE, "").strip()
    if credential:
        return credential

    user_path, local_path = credential_config_paths()
    for path in (user_path, local_path):
        if not path.is_file():
            continue
        credential = str(dotenv_values(path).get(ENVIRONMENT_VARIABLE) or "").strip()
        if credential:
            return credential

    raise RuntimeError(
        f"{ENVIRONMENT_VARIABLE} is not configured. Set it in the environment, "
        f"or create {user_path} or {local_path} with {ENVIRONMENT_VARIABLE}=<token>."
    )

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

    logger.debug("Authenticated to Activate")
    logger.debug("Full login response: %s", response.text)

    return session
