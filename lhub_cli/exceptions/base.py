class LhCliBaseException(BaseException):
    """There was a generic exception that occurred while handling your
    request.

    Catching this exception will catch *all* custom exceptions from this package
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CLIValueError(LhCliBaseException, ValueError):
    """Deliberate ValueError exceptions from lhub-cli"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PathNotFound(LhCliBaseException):
    """File path not found"""
    message = "File or directory not found"

    def __init__(self, path, message=None, *args, **kwargs):
        self.path = path
        if message:
            self.message = message
        elif self.path:
            self.message += f": {self.path}"
        super().__init__(*args, **kwargs)
