#!/usr/bin/env python3

import argparse
import lhub_cli
from lhub_cli.common.output import print_fancy_lists


def get_args():
    _parser = argparse.ArgumentParser(description="Search Cases")
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    return lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_list_output_args=True
    )


def rename_dict_key(dict_var: (dict, list), old_key, new_key):
    """Rename a key without redefining the object or changing the order of keys"""
    if isinstance(dict_var, dict):
        if old_key not in dict_var:
            raise KeyError(f"No key found by name: {old_key}")
        elif new_key in dict_var:
            raise KeyError(f"Key already exists with new name: {new_key}")
        for k in list(dict_var.keys()):
            if k == old_key:
                dict_var[new_key] = dict_var.pop(old_key)
            else:
                dict_var[k] = dict_var.pop(k)
    elif isinstance(dict_var, list):
        for n in range(len(dict_var)):
            rename_dict_key(dict_var[n], old_key, new_key)


# Must be run outside of main in order for the full effect of verbose logging
args, logger = get_args()
log = logger.log


def main():
    log.debug("Starting")
    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(instance_name=args.instance_name)

    username = "paul.ritchey@logichub.com"
    query = f'IssueType = "case" AND StatusType != closed AND title ~ "LogicHub app user" AND title ~ "{username}"'

    # Choose the CLI action to execute. Below is an example for
    results = cli.session.actions.search_cases_advanced(query=query, limit=None, includeWorkflow=False)

    # Pick and choose what columns you want, make any desired tweaks, etc.
    # For sample purposes, rename "id" column
    rename_dict_key(results, "id", "case ID")

    print_fancy_lists(
        results,
        output_type=args.output,
        table_format=args.table_format,
        ordered_headers=["case ID", "status", "priority", "issueType", "reporter", "assignee", "title", "createdAt", "modifiedAt"],
        output_file=args.file,
        # sort_order=["case ID"],
        sort_order=[{"name": "case ID", "reverse": True}],
    )


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
