from cryptography.fernet import Fernet
import os

KEY_FILE = "encryption.key"


def get_or_create_key():
    """Get existing encryption key or generate a new one.

    The key is stored in a local file. In production, use a
    secrets manager (e.g. AWS KMS, HashiCorp Vault).
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()

    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


def encrypt_data(data):
    """Encrypt data using Fernet (AES-128-CBC with HMAC)."""
    key = get_or_create_key()
    f = Fernet(key)
    return f.encrypt(data)


def decrypt_data(data):
    """Decrypt data using Fernet (AES-128-CBC with HMAC)."""
    key = get_or_create_key()
    f = Fernet(key)
    return f.decrypt(data)
