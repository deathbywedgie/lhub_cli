from .base import LhCliBaseException


class EncryptionKeyError(LhCliBaseException, IOError):
    """Exceptions related to encryption and decryption"""
    message = "Encryption key exception"

    def __init__(self, message=None, *args, **kwargs):
        super().__init__(message=message, *args, **kwargs)
