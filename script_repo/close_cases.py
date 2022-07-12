#!/usr/bin/env python3

import argparse
import asyncio

import lhub_cli
from lhub_cli.common.output import print_fancy_lists
from lhub_cli.common.shell import query_yes_no


def get_args():
    _parser = argparse.ArgumentParser(description="Search Cases")
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    _parser.add_argument("-l", "--limit", default=None, type=int, help="Limit the number of results")

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


async def close_case(case_id, cli_session: lhub_cli.LogicHubCLI):
    log.warn("Closing case", case_id=case_id)
    _ = cli_session.session.api.case_update(case_id, status="Resolved")


async def close_all_cases(case_ids: list, cli_session: lhub_cli.LogicHubCLI):
    await asyncio.gather(*[close_case(case_id=case_id, cli_session=cli_session) for case_id in case_ids])


# Must be run outside of main in order for the full effect of verbose logging
args, logger = get_args()
log = logger.log


def main():
    # Prompt the user for the query to execute
    query = get_query()

    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(instance_name=args.instance_name)

    results = cli.session.actions.search_cases_advanced(query=query, limit=args.limit, includeWorkflow=False)
    log.info(f"Query complete. Total results: {len(results)}")

    print_fancy_lists(
        results,
        output_type=args.output,
        table_format=args.table_format,
        ordered_headers=["id", "status", "priority", "issueType", "reporter", "assignee", "title", "createdAt", "modifiedAt"],
        output_file=args.file,
        # sort_order=["id"],
        sort_order=[{"name": "createdAt", "reverse": True}],
    )

    if not results or not query_yes_no("\nProceed with closing cases?"):
        return
    cases = [r["id"] for r in results]
    asyncio.run(close_all_cases(case_ids=cases, cli_session=cli))


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
