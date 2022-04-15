from .base import LhCliBaseException


class EncryptionKeyError(LhCliBaseException, IOError):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
