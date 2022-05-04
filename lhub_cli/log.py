import logging
import structlog
from sys import stdout


# Alias so that lhub_cli scripts can point to this without risk of having to change it later if I move away from structlog
# Mainly just used for type parsing/tab completions within PyCharm and other dev tools
ExpectedLoggerTypes = [structlog.types.BindableLogger]


class Logging:
    level = "INFO"

    def __init__(self, self_obj=None, log_level=None, **kwargs):
        log_level = log_level or Logging.level
        self.log = generate_logger(self_obj=self_obj or self, level=log_level, **kwargs)


def generate_logger(self_obj, instance_name=None, level=None, include_file_info=False, **kwargs):
    """
    Generate a logger object for use throughout lhub and lhub_cli

    :returns: Logger object for lhub and lhub_cli logging
    :rtype: ExpectedLoggerTypes
    """
    level = level.upper().strip() if level else Logging.level

    # See logging.Formatter doc string for details on all available variables
    logging_format = "%(message)s"
    if include_file_info or level == "DEBUG":
        logging_format = "[%(levelname)s][%(name)s][%(module)s] " + logging_format

    logging.basicConfig(
        format=logging_format,
        stream=stdout,
        level=level
    )
    if level == logging.DEBUG:
        # Defining root_log (i.e. no logger name provided in getLogger) deliberately affects the "requests" module (via urllib3) and any other module using builtin logging
        root_log = logging.getLogger()
        root_log.setLevel(level)

    # lhub_cli itself will use its own logger
    logger = logging.getLogger(self_obj.__name__ if self_obj else __name__)
    if level:
        logger.setLevel(level)

    # if "instance_name" was passed and a connection key was not already passed, add it automatically
    if instance_name and kwargs.get("connection"):
        kwargs["connection"] = instance_name
    structlog.configure()
    final_log = structlog.wrap_logger(logger, **kwargs)
    final_log.level = level
    return final_log
