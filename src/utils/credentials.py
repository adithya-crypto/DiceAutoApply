"""
Secure credential storage using keyring (OS keychain)
Falls back to config file if keyring is unavailable
"""

import logging
from typing import Optional, Tuple

# Service name for keyring
SERVICE_NAME = "DiceAutoApply"

# Try to import keyring
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logging.warning("keyring not available, credentials will be stored in config file")


def store_credentials(email: str, password: str) -> bool:
    """
    Store credentials securely using keyring.

    Args:
        email: User's email address
        password: User's password

    Returns:
        True if stored successfully, False otherwise
    """
    if not KEYRING_AVAILABLE:
        return False

    try:
        # Store email as the username key
        keyring.set_password(SERVICE_NAME, "email", email)
        # Store password under the email key
        keyring.set_password(SERVICE_NAME, email, password)
        return True
    except Exception as e:
        logging.error(f"Failed to store credentials in keyring: {e}")
        return False


def get_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve credentials from keyring.

    Returns:
        Tuple of (email, password), or (None, None) if not found
    """
    if not KEYRING_AVAILABLE:
        return None, None

    try:
        email = keyring.get_password(SERVICE_NAME, "email")
        if email:
            password = keyring.get_password(SERVICE_NAME, email)
            return email, password
        return None, None
    except Exception as e:
        logging.error(f"Failed to get credentials from keyring: {e}")
        return None, None


def delete_credentials() -> bool:
    """
    Delete stored credentials from keyring.

    Returns:
        True if deleted successfully, False otherwise
    """
    if not KEYRING_AVAILABLE:
        return False

    try:
        email = keyring.get_password(SERVICE_NAME, "email")
        if email:
            keyring.delete_password(SERVICE_NAME, email)
            keyring.delete_password(SERVICE_NAME, "email")
        return True
    except Exception as e:
        logging.error(f"Failed to delete credentials from keyring: {e}")
        return False


def has_keyring() -> bool:
    """Check if keyring is available."""
    return KEYRING_AVAILABLE


def get_credential_storage_type() -> str:
    """Get the type of credential storage being used."""
    if KEYRING_AVAILABLE:
        try:
            backend = keyring.get_keyring()
            return f"Keyring ({backend.__class__.__name__})"
        except Exception:
            return "Keyring"
    return "Config file (plaintext)"
