#!/usr/bin/env python3

import argparse
import sys

from lhub.log import Logger

import lhub_cli

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_OUTPUT = "json"


def get_args():
    parser = argparse.ArgumentParser(description="List all users from one or more LogicHub instances")

    # Required inputs
    parser.add_argument("instance_names", nargs="*", help="Names of specific instances from stored config (default: show all)")

    # Optional inputs
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Add standard output arg definitions
    lhub_cli.common.args.add_script_output_args(parser, default=DEFAULT_OUTPUT)

    _args = parser.parse_args()
    _args.log_level = DEFAULT_LOG_LEVEL
    if _args.debug:
        _args.log_level = "DEBUG"

    return _args


def main():
    args = get_args()
    log = Logger(log_level=args.log_level)

    config = lhub_cli.connection_manager.LogicHubConnection()
    if args.instance_names:
        instances = args.instance_names
    else:
        instances = config.config.list_configured_instances()

    output = []
    for i in instances:
        # If the instance name does not already exist as a saved connection, this will
        cli = lhub_cli.LogicHubCLI(i, log_level=args.log_level)

        log.info(f"Connecting to {i}")
        result = cli.session.actions.list_users(hide_inactive=True)

        for user in result['data']:
            username = user["name"]
            groups = user['groups']
            entry = {
                "connection name": i,
                "hostname": cli.session.api.url.server_name,
                "username": username,
            }
            is_admin = False
            for g in groups:
                if g['name'] == "Admin":
                    is_admin = True
            entry["is admin"] = is_admin
            output.append(entry)

    # Sort the results by connection name, hostname, and then username (function lists reverse order)
    output = sorted(output, key=lambda e: (e['username'], e['hostname'], e['connection name']))

    lhub_cli.common.output.print_fancy_lists(
        results=output,
        output_type=args.output_type,
        table_format=args.table_format,
        ordered_headers=None,
        output_file=args.file
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=sys.stderr)
