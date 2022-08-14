#!/usr/bin/env python3
import argparse
import re
import sys

import lhub_cli


def parse_and_validate_args():
    # Range of available args and expected input
    _parser = argparse.ArgumentParser(description="Remotely execute a LogicHub command")

    # Required inputs
    _parser.add_argument("instance", metavar="INSTANCE", type=str, help="Name of the instance as defined in credentials.json")
    _parser.add_argument("command", metavar="COMMAND", type=str, help="Name of the remote LogicHub command to execute")

    # Optional inputs
    _parser.add_argument("params", metavar="PARAMS", nargs='*', help="Command parameters (inputs) as key-value pairs")
    _parser.add_argument("--fix_json", action="store_true", help="Automatically fix JSON formatting issues")

    fields = _parser.add_mutually_exclusive_group()

    fields.add_argument(
        "--fields", type=str, metavar="<FIELDS>", default="",
        help="Top level fields to display")

    fields.add_argument(
        "--drop", type=str, metavar="<FIELDS>", default="",
        help="Top level fields to drop")

    connection = _parser.add_argument_group('connection')
    connection.add_argument("-ti", "--timeout", metavar="<sec>", type=int, default=120, help="HTTP request timeout, except for logon (default: 120)")
    connection.add_argument("-tl", "--timeout_logon", metavar="<sec>", type=int, default=20, help="Logon timeout (default: 20)")

    _final_args, _logger = lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_credential_file_arg=True,
        include_list_output_args=True,
        include_logging_args=True,
        # default_log_level="INFO",
    )

    if not _final_args.instance:
        log.critical("Instance cannot be blank")
        sys.exit(1)
    if not _final_args.command:
        log.critical("command cannot be blank")
        sys.exit(1)

    return _final_args, _logger.log


# Must be run outside of main in order for the full effect of verbose logging
args, log = parse_and_validate_args()


def main():
    command_parameters = {}
    for i in args.params:
        _parts = re.search("^([^=]+)=(.*)", i)
        if not _parts:
            log.critical(f"Parameters must be key-value pairs. Invalid input: {i}")
            sys.exit(1)
        command_parameters[_parts.group(1)] = _parts.group(2)

    fields = [x.strip() for x in args.fields.split(',') if x.strip()]
    drop_fields = [x.strip() for x in args.drop.split(',') if x.strip()]

    shell = lhub_cli.LogicHubCLI(
        args.instance,
        http_timeout_login=args.timeout_logon,
        http_timeout_default=args.timeout
    )
    log.debug(f"Logon timeout: {args.timeout_logon}")
    log.debug(f"Other HTTP timeout: {args.timeout}")

    command = lhub_cli.features.commands.Command(
        session=shell.session,
        verify_ssl=shell.session.api.verify_ssl,
        output_type=args.output,
        table_format=args.table_format
    )
    command.run_command(command=args.command, fix_json=args.fix_json, fields=fields, drop=drop_fields, output_file=args.file, **command_parameters)


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
