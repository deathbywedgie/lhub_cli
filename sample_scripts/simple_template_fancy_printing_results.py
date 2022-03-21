#!/usr/bin/env python3

import argparse

import lhub_cli
from lhub_cli.common.output import print_fancy_lists


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description="Simple script for testing API calls")

    # Inputs required from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    # Add standard output arg definitions
    lhub_cli.common.args.add_script_output_args(parser)

    # Optional args:
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


args = get_args()

# If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
cli = lhub_cli.LogicHubCLI(
    instance_name=args.instance_name,

    # If the --debug option was passed by the user, set log level to debug, otherwise leave it default
    log_level="DEBUG" if args.debug else None
)

results = cli.session.actions.list_users(hide_inactive=True)
# dict_keys(['userId', 'name', 'groups', 'role', 'authenticationType', 'preferences', 'isEnabled', 'isDeleted'])
results = [{"userId": r['userId'], "name": r['name'], "role": r['role']['value']} for r in results["data"]]

print_fancy_lists(
    results,
    output_type=args.output_type,
    table_format=args.table_format,
    # ordered_headers=None,
    output_file=args.file,
    # sort_order=None,
)
