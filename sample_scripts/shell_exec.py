#!/usr/bin/env python3

import argparse
import lhub

import lhub_cli


def parse_and_validate_args():
    _parser = argparse.ArgumentParser(description="Launch the LogicHub remote shell")
    _parser.add_argument("instance", metavar="INSTANCE", type=str, nargs="?", default=None, help="Name/label of the instance to which you wish to connect")

    connection = _parser.add_argument_group('connection')
    connection.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL warnings")
    connection.add_argument("-ti", "--timeout", metavar="<sec>", type=int, default=120, help="HTTP request timeout, except for logon (default: 120)")

    return lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_logging_args=True,
        # default_log_level="INFO",
    )


args, _ = parse_and_validate_args()


def main():
    lhub.api.LogicHubAPI.http_timeout_default = args.timeout
    lhub_cli.shell.Shell(log_level=args.LOG_LEVEL).cmdloop()


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
