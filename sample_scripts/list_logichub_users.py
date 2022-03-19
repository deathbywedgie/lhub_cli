#!/usr/bin/env python3

import argparse
import json
import sys

from lhub.log import Logger
from tabulate import tabulate, tabulate_formats

import lhub_cli

LOG_LEVEL = "INFO"


def get_args():
    parser = argparse.ArgumentParser(description="List all users from one or more LogicHub instances")

    # Inputs required from user
    parser.add_argument("instance_names", nargs="*", help="Names of specific instances from stored config (default: show all)")

    # Optional args:
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument(
        "-f", dest="format", type=str, default=None, choices=tabulate_formats, metavar=f"{{{', '.join(tabulate_formats)}}}",
        help=f"Optional: print output in a table with a specified format (default: None)"
    )
    _args = parser.parse_args()
    if _args.debug:
        global LOG_LEVEL
        LOG_LEVEL = "DEBUG"

    return parser.parse_args()


def main():
    global LOG_LEVEL
    args = get_args()
    log = Logger(log_level=LOG_LEVEL)

    config = lhub_cli.connection_manager.LogicHubConnection()
    if args.instance_names:
        instances = args.instance_names
    else:
        instances = config.config.list_configured_instances()

    output = []
    for i in instances:
        # If the instance name does not already exist as a saved connection, this will
        cli = lhub_cli.LogicHubCLI(i, log_level=LOG_LEVEL)

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

    output = sorted(output, key=lambda e: (e['username'], e['hostname'], e['connection name']))
    if args.format:
        output = tabulate(
            tabular_data=[x.values() for x in output],
            headers=output[0].keys(),
            tablefmt=args.format
        )
    else:
        output = json.dumps(output, indent=2)

    print(output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=sys.stderr)
