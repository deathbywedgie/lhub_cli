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
    cred_files = lhub_cli.list_credential_files()
    existing_creds_str = ''
    if cred_files:
        existing_creds_str = f', existing: {cred_files}'
    parser = argparse.ArgumentParser(description="List all commands from one or more LogicHub instances")

    # Required inputs
    parser.add_argument("instance_names", nargs="*", help="Names of specific instances from stored config (default: show all)")
    parser.add_argument("-cred", "--credentials_file_name", default=None, help=f"Alternate credentials file name to use (default: \"credentials\"{existing_creds_str})")

    # Add standard output arg definitions:
    #         "-f", "--file" (Also write output to a file)
    #         "-o", "--output" (Output style, e.g. table, csv, json, json-pretty)
    #         "-t", "--table_format" (for output style of table, set a specific table style, such as plain, grid, and jira)
    # Also sets logging automatically
    return lhub_cli.common.args.finish_parser_args(
        parser,
        default_output=DEFAULT_OUTPUT,
        # Set include_log_level to False to drop log arg
        # include_log_level=False
    )


def main():
    args = get_args()
    log = args.LOGGER

    if args.instance_names:
        instances = args.instance_names
    else:
        config = lhub_cli.connection_manager.LogicHubConnection(
            credentials_file_name=args.credentials_file_name
        )
        instances = sorted(config.all_instances)

    # For all available attributes, set: attributes = "*"
    # attributes = ["connection name", "hostname", "name", "id", "flowId", "owner", "last_updated", "command_status"]
    attributes = "*"

    combined_results = []
    if instances:
        instance_sessions = {}
        instance_count = len(instances)
        cycle = range(instance_count)

        if args.level != "DEBUG":
            cycle = progressbar.progressbar(cycle)
            print(f"Verifying connections")
        for n in cycle:
            log.debug(f"Verifying connection {n + 1}/{instance_count}")
            instance_sessions[instances[n]] = lhub_cli.LogicHubCLI(
                instance_name=instances[n],
                credentials_file_name=args.credentials_file_name
            )

        cycle = range(instance_count)
        if args.level != "DEBUG":
            cycle = progressbar.progressbar(cycle)
            print(f"Fetching commands")
        for n in cycle:
            _instance = instances[n]
            cli = instance_sessions[instances[n]]
            log.debug(f"Fetching commands from {cli.instance_name} ({n + 1}/{instance_count})")
            combined_results.extend(
                cli.actions.list_commands(
                    print_output=False,
                    show_hostname=True,
                    attributes=attributes,
                )
            )

    print_fancy_lists(
        results=combined_results,
        output_type=args.output,
        table_format=args.table_format,
        output_file=(args.file or None),

        # Enable to provide columns to keep, in order
        # ordered_headers=[],

        # Enable to provide a list of columns for custom sorting
        # sort_order=[],

        # Change to "False" to always print output even if writing to a file
        file_only=(True if args.file else False)
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=stderr)
