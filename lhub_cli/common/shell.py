import sys


def query_yes_no(question, default: (str, bool) = None):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    # Borrowed from here: https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
    valid_yes = ["yes", "y", "ye"]
    valid_no = ["no", "n"]
    if default is not None:
        if isinstance(default, str):
            default = default.lower().strip()
            assert default in valid_yes + valid_no, f"Invalid input for default value: {default}"
            # Convert to boolean
            default = default in valid_yes

    if default is None:
        prompt = " [y/n] "
    elif default is True:
        prompt = " [Y/n] "
    elif default is False:
        prompt = " [y/N] "
    else:
        raise ValueError(f"Invalid input for default value: {default}")

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower().strip()
        if choice and choice in valid_yes + valid_no:
            return choice in valid_yes
        if not choice and default is not None:
            return default
        else:
            sys.stdout.write("Please respond with one of the following: y/n/yes/no\n\n")


def main_script_wrapper(func, *args, **kwargs):
    from ..exceptions.base import LhCliBaseException
    from lhub.exceptions.base import LhBaseException
    from requests.exceptions import RequestException

    logger = kwargs.pop("logger", None)
    if not logger:
        from ..log import Logging
        logger = Logging.DEFAULT_LOGGER
        if not logger:
            _logger = Logging()
            logger = _logger.log
    exit_code = 0
    try:
        func(*args, **kwargs)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print()
        logger.critical("Canceled by user")
        print("Control-C Pressed, stopping...", file=sys.stderr)
    except (LhBaseException, LhCliBaseException, RequestException) as e:
        exit_code = 1
        message = getattr(e, "message", None)
        if not message and isinstance(e, (LhBaseException, LhCliBaseException)):
            message = str(e)
        if not message:
            message = repr(e)
        logger.critical(f"Failed with exception: {message}")

        if last_response_status := getattr(e, "last_response_status", None):
            logger.debug(f"Last status: {last_response_status}")
        if last_response_text := getattr(e, "last_response_text", None):
            logger.debug.print(f"Last server response: {last_response_text}")
    except:
        logger.exception("Script failed with exception")
    sys.exit(exit_code)
