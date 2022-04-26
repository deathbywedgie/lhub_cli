import sys

_LOG_LEVEL_MAP = {"debug": 7, "info": 6, "notice": 5, "warn": 4, "error": 3, "crit": 2, "alert": 1, "fatal": 0}
LOG_LEVELS = _LOG_LEVEL_MAP.keys()


def generate_log_session_id(obj):
    id_str = str(hex(id(obj)))
    return id_str.removeprefix('0x')


# ToDo Placeholder for real logging: figure out how to do the same w/ the logger package and get rid of this
class DefaultLogger:
    __log_level = "INFO"
    default_log_level = "INFO"

    def __init__(self, session_prefix=None, log_level=None):
        self.level = log_level if log_level else self.default_log_level
        self.session_prefix = (session_prefix if session_prefix is not None else generate_log_session_id(self)).strip()
        if self.session_prefix:
            self.session_prefix = f"[{self.session_prefix}] "

    @property
    def level(self):
        if self.__log_level.lower() not in LOG_LEVELS:
            raise ValueError(f"Invalid log level: {self.__log_level}")
        return self.__log_level

    @level.setter
    def level(self, val: str):
        if val.lower() not in LOG_LEVELS:
            raise ValueError(f"Invalid log level: {val}")
        self.__log_level = val.upper()

    # temporary to make this fit logging package as closely as possible until we phase this out
    def setLevel(self, level: str):
        self.level = level

    def __print(self, level, msg):
        level_num = _LOG_LEVEL_MAP[level.lower()]
        output_file = sys.stdout if level_num >= 5 else sys.stderr
        current_level_num = _LOG_LEVEL_MAP[self.level.lower()]
        if current_level_num >= level_num:
            print(f"{self.session_prefix}[{level.upper()}] {msg}", file=output_file)
        if level_num == 0:
            sys.exit(1)

    def debug(self, msg):
        self.__print("debug", msg)

    def info(self, msg):
        self.__print("info", msg)

    def notice(self, msg):
        self.__print("notice", msg)

    def warning(self, msg):
        self.__print("warn", msg)

    def warn(self, msg):
        self.warning(msg)

    def error(self, msg):
        self.__print("error", msg)

    def critical(self, msg):
        self.__print("crit", msg)

    def alert(self, msg):
        self.__print("alert", msg)

    def fatal(self, msg):
        self.__print("fatal", msg)
