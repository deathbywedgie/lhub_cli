#!/usr/bin/env python3

import argparse
import lhub
from logging import _nameToLevel as AllowedLogLevels

from lhub_cli.shell import Shell


# ToDo Add log level option
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
        choices=AllowedLogLevels,
        help="Log level (default: info)"
    )

    connection = parser.add_argument_group('connection')

    connection.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL warnings")
    connection.add_argument("-t", "--timeout", metavar="<sec>", type=int, default=120, help="HTTP request timeout, except for logon (default: 120)")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_and_validate_args()

    lhub.api.LogicHubAPI.http_timeout_default = args.timeout
    # log = lhub.log.Logger()
    # log.debug(f"Setting custom HTTP timeout: {args.timeout}")

    # ToDo Add option to provide the connection label up front when the script is invoked
    Shell(log_level=args.log_level).cmdloop()
