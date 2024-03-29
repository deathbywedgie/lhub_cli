#!/usr/bin/env python3

import argparse
import lhub_cli
from lhub_cli.common.output import print_fancy_lists

# ToDo Move a lot of this functionality into actions


def get_args():
    _parser = argparse.ArgumentParser(description="Search Cases")
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    _parser.add_argument("-l", "--limit", default=None, type=int, help="Limit the number of results")

    return lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_list_output_args=True
    )


def get_query():
    query = ""
    while True:
        print("Type or paste your case query below. Press enter twice when finished.\n")
        while True:
            query_input = input().strip()
            if query_input:
                if query:
                    query += " "
                query += query_input
            elif query:
                log.info("Query accepted")
                log.debug(f"Full query: {query}")
                return query
            else:
                break


# Must be run outside of main in order for the full effect of verbose logging
args, logger = get_args()
log = logger.log


def main():
    log.debug("Starting")
    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(instance_name=args.instance_name)

    # Query string, as you would enter for an advanced case search in the UI
    query = get_query()

    # To receive more results than the default of 25, add "limit=N" as an input,
    # where "N" is the new row limit. Set to -1 for unlimited.
    results = cli.session.actions.search_cases_advanced(query=query, includeWorkflow=False, limit=args.limit)
    log.info(f"Query complete. Total results: {len(results)}")

    print_fancy_lists(
        results,
        output_type=args.output,
        table_format=args.table_format,
        ordered_headers=["id", "status", "priority", "issueType", "reporter", "assignee", "title", "createdAt", "modifiedAt"],
        output_file=args.file,
        # sort_order=["createdAt"],
        sort_order=[{"name": "createdAt", "reverse": True}],
    )


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
