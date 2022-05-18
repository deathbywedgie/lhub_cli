#!/usr/bin/env python3

import argparse

import lhub_cli
from lhub_cli.common.output import print_fancy_lists


def get_args():
    _parser = argparse.ArgumentParser(description="Simple script for testing API calls")
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    return lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_list_output_args=True
    )


args, _ = get_args()

# If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
cli = lhub_cli.LogicHubCLI(instance_name=args.instance_name)

results = cli.session.actions.list_users(hide_inactive=True)
# dict_keys(['userId', 'name', 'groups', 'role', 'authenticationType', 'preferences', 'isEnabled', 'isDeleted'])
results = [{"userId": r['userId'], "name": r['name'], "role": r['role']['value']} for r in results["data"]]

print_fancy_lists(
    results,
    output_type=args.output,
    table_format=args.table_format,
    # ordered_headers=None,
    output_file=args.file,
    # sort_order=None,
)
