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
