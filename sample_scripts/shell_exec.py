#!/usr/bin/env python3

from lhub_cli.connection_manager import LogicHubConnection
import argparse
import lhub
from lhub_cli.shell import Shell


def parse_and_validate_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Launch the LogicHub remote shell")

    # Required input
    parser.add_argument("instance", metavar="INSTANCE", type=str, nargs="?", default=None, help="Name/label of the instance to which you wish to connect")

    parser.add_argument(
        "-log", "--log_level",
        metavar="<level>",
        type=str,
        default="info",
        choices=lhub.log.LOG_LEVELS,
        help="Log level (default: info)"
    )

    connection = parser.add_argument_group('connection')

    connection.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL warnings")
    connection.add_argument("-t", "--timeout", metavar="<sec>", type=int, default=120, help="HTTP request timeout, except for logon (default: 120)")
    connection.add_argument("-tl", "--timeout_logon", metavar="<sec>", type=int, default=20, help="Logon timeout (default: 20)")

    # take in the arguments provided by user
    _args = parser.parse_args()

    lhub.log.log_level = _args.log_level
    # Logger.default_log_level = _args.log_level

    lhub.LogicHub.http_timeout_login = _args.timeout_logon
    # lhub.log.debug(f"Logon timeout: {_args.timeout_logon}")

    lhub.LogicHub.http_timeout_default = _args.timeout
    # lhub.log.debug(f"Other HTTP timeout: {_args.timeout}")

    # if _args.ignore_ssl:
    #     lhub.log.debug(f"SSL verification disabled")
    #     # lhub.LogicHub.verify_ssl = False

    return _args


if __name__ == '__main__':
    args = parse_and_validate_args()
    # Shell.session = LogicHubConnection(instance_alias=args.instance)
    Shell().cmdloop()
