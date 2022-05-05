class LhCliBaseException(Exception):
    """There was a generic exception that occurred while handling your
    request.

    Catching this exception will catch *all* custom exceptions from this package
    """
    message = "An exception was raised"

    def __init__(self, message=None, input_var=None, *args, **kwargs):
        self.input = input_var
        if message:
            self.message = message
        elif input_var:
            self.message += f": {input_var}"
        super().__init__(*args, **kwargs)


class CLIValueError(LhCliBaseException, ValueError):
    """Deliberate ValueError exceptions from lhub-cli"""
    "A ValueError was triggered by lhub_cli"

    def __init__(self, input_var=None, message=None, *args, **kwargs):
        super().__init__(message=message, input_var=input_var, *args, **kwargs)
