#!/usr/bin/env python3

import argparse
import sys

import lhub_cli
from lhub_cli.common.output import print_fancy_lists
import progressbar

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_OUTPUT = "table"


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

    if args.instance_names:
        instances = args.instance_names
    else:
        config = lhub_cli.connection_manager.LogicHubConnection()
        instances = config.config.list_configured_instances()

    # For all available attributes, set: attributes = "*"
    attributes = ["email", "is_admin", "groups"]

    combined_results = []
    for n in progressbar.progressbar(range(len(instances))):
        _instance = instances[n]
        cli = lhub_cli.LogicHubCLI(_instance, log_level=args.log_level)
        cli.session.api.log.debug(f"Connected to {_instance}")
        combined_results.extend(
            cli.actions.list_users(
                attributes=attributes,
                print_output=False,
                # return_results=True,
                show_hostname=True,
                # hide_inactive=False,
                # sort_order=[]
            )
        )

    # Set to None in order to leave all results in the default order, in the order of connections as they were requested
    sort_order = ["connection name"]

    file_only = False
    if args.file:
        file_only = True
    print_fancy_lists(combined_results, sort_order=sort_order, output_file=args.file or None, file_only=file_only)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=sys.stderr)
