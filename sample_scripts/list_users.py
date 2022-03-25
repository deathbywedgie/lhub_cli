#!/usr/bin/env python3

import argparse
from sys import stderr

import lhub_cli
from lhub_cli.common.output import print_fancy_lists
import progressbar

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_OUTPUT = "table"


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description="List all users from one or more LogicHub instances")

    # Required inputs
    parser.add_argument("instance_names", nargs="*", help="Names of specific instances from stored config (default: show all)")

    # Optional inputs
    parser.add_argument("-i", "--inactive", action="store_true", help="Include inactive users in the results")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Add standard output arg definitions:
    #         "-f", "--file" (Also write output to a file)
    #         "-o", "--output" (Output style, e.g. table, csv, json, json-pretty)
    #         "-t", "--table_format" (for output style of table, set a specific table style, such as plain, grid, and jira)
    lhub_cli.common.args.add_script_output_args(parser, default_output=DEFAULT_OUTPUT)

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
        instances = sorted(config.all_instances)

    # For all available attributes, set: attributes = "*"
    # Examples: ["is_admin", "email", "groups", "is_deleted", "is_enabled", "auth_type", "id"]
    attributes = ["email", "is_admin", "groups"]

    show_inactive = args.inactive
    if args.inactive:
        for a in ["is_enabled", "is_deleted"]:
            if a not in attributes:
                attributes.append(a)

    combined_results = []
    for n in progressbar.progressbar(range(len(instances))):
        cli = lhub_cli.LogicHubCLI(
            instance_name=instances[n],
            log_level=args.log_level
        )
        cli.session.api.log.debug(f"Connected to {cli.instance_name}")
        combined_results.extend(
            cli.actions.list_users(
                print_output=False,
                show_hostname=True,
                attributes=attributes,
                hide_inactive=show_inactive is False,
            )
        )

    print_fancy_lists(
        results=combined_results,
        output_type=args.output,
        table_format=args.table_format,
        output_file=(args.file or None),

        # Enable to provide columns to keep, in order
        # ordered_headers=[],

        # Set to None in order to leave all results in the default order, in the order of connections as they were requested
        sort_order=["connection name"],

        # Change to False to always print output even if writing to a file
        file_only=(True if args.file else False)
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=stderr)
