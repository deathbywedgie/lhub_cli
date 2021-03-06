#!/usr/bin/env python3
import argparse
import re
import sys

import lhub

import lhub_cli
from lhub_cli.features.commands import TABLE_FORMATS


# ToDo:
#  * Add an argparse option for setting the result limit to return. Default is 25.
#  * Rework lhub_cli & this file so that lhub_cli is *only* for stuff that should still be there when this switches to a shell
#  * Get rid of references to lhub. Sample scripts shouldn't have to know about lhub. lhub_cli should handle everything.
#  * Try to move all logging out of lhub

def log_fatal(msg):
    print(f"[FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def parse_and_validate_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Remotely execute a LogicHub command")

    # Required input
    parser.add_argument("instance", metavar="INSTANCE", type=str, help="Name of the instance as defined in credentials.json")
    parser.add_argument("command", metavar="COMMAND", type=str, help="Name of the remote LogicHub command to execute")

    # Optional input
    parser.add_argument("params", metavar="PARAMS", nargs='*', help="Command parameters (inputs) as key-value pairs")

    parser.add_argument(
        "--log_level",
        type=str,
        default="info",
        choices=lhub.log.LOG_LEVELS,
        help="Log level (default: info)"
    )

    output = parser.add_argument_group('output')

    output.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Also write output to a file")

    fields = output.add_mutually_exclusive_group()

    fields.add_argument(
        "--fields",
        type=str,
        metavar="<FIELDS>",
        default="",
        help="Top level fields to display")

    fields.add_argument(
        "--drop",
        type=str,
        metavar="<FIELDS>",
        default="",
        help="Top level fields to drop")

    output.add_argument("--fix_json", action="store_true", help="Automatically fix JSON formatting issues")

    output.add_argument(
        "-o", "--output",
        dest="output_type",
        type=str,
        default="table",
        choices=lhub_cli.features.commands.Command.supported_output_types,
        help="Output style (default: table)")

    # https://github.com/astanin/python-tabulate#table-format
    output.add_argument(
        "--table_format",
        type=str,
        default=None,
        choices=TABLE_FORMATS,
        help="Table format, ignored if output type is not table (\"tablefmt\" from tabulate python package)"
    )

    connection = parser.add_argument_group('connection')

    connection.add_argument("-t", "--timeout", metavar="<sec>", type=int, default=120, help="HTTP request timeout, except for logon (default: 120)")
    connection.add_argument("-tl", "--timeout_logon", metavar="<sec>", type=int, default=20, help="Logon timeout (default: 20)")

    # take in the arguments provided by user
    _args = parser.parse_args()

    if not _args.instance:
        log_fatal("Instance cannot be blank")
    if not _args.command:
        log_fatal("command cannot be blank")

    lhub.LogicHub.http_timeout_login = _args.timeout_logon
    lhub.LogicHub.http_timeout_default = _args.timeout

    return _args


def main():
    args = parse_and_validate_args()
    command_parameters = {}
    for i in args.params:
        _parts = re.search("^([^=]+)=(.*)", i)
        if not _parts:
            log_fatal(f"Parameters must be key-value pairs. Invalid input: {i}")
        command_parameters[_parts.group(1)] = _parts.group(2)

    fields = [x.strip() for x in args.fields.split(',') if x.strip()]
    drop_fields = [x.strip() for x in args.drop.split(',') if x.strip()]

    shell = lhub_cli.LogicHubCLI(args.instance, log_level=args.log_level)
    shell.log.debug(f"Logon timeout: {args.timeout_logon}")
    shell.log.debug(f"Other HTTP timeout: {args.timeout}")

    try:
        command = lhub_cli.features.commands.Command(
            session=shell.session,
            verify_ssl=shell.session.api.verify_ssl,
            output_type=args.output_type,
            table_format=args.table_format
        )
        command.run_command(command=args.command, fix_json=args.fix_json, fields=fields, drop=drop_fields, output_file=args.file, **command_parameters)
    except lhub.exceptions.LhBaseException as e:
        shell.log.fatal(f'FAILED: {str(e)}')
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=sys.stderr)
