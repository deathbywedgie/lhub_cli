import logging
import structlog
from sys import stdout


# Alias so that lhub_cli scripts can point to this without risk of having to change it later if I move away from structlog
# Mainly just used for type parsing/tab completions within PyCharm and other dev tools
ExpectedLoggerTypes = [structlog.types.BindableLogger]


class Logging:
    level = None

    def __init__(self, self_obj=None, log_level=None, **kwargs):
        log_level = log_level or Logging.level
        self.log = generate_logger(self_obj=self_obj or self, log_level=log_level, **kwargs)


def generate_logger(self_obj, instance_name=None, log_level=None, **kwargs):
    log_level = log_level or Logging.level
    if log_level:
        log_level = log_level.upper().strip()
    if instance_name:
        kwargs["connection"] = instance_name
    logging.basicConfig(format="%(message)s", stream=stdout, level=log_level)
    if log_level == "DEBUG":
        # Defining root_log (no logger name provided in getLogger) affects the requests module and any other module using the builtin logging module
        root_log = logging.getLogger()
        root_log.setLevel(log_level)
    log = logging.getLogger(str(hex(id(self_obj))).removeprefix('0x'))
    if log_level:
        log.setLevel(log_level)
    structlog.configure()
    return structlog.wrap_logger(log, **kwargs)
