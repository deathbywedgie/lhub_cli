#!/usr/bin/env python3

"""
List all users across one or more LogicHub instances

Additional packages required:
* progressbar
"""

import argparse
import threading

import progressbar

import lhub_cli
from lhub_cli.common.output import print_fancy_lists

# Configurable defaults
THREAD_LIMIT = 20


def get_args():
    _parser = argparse.ArgumentParser(description="List all users from one or more LogicHub instances")
    _parser.add_argument("instance_names", nargs="*", help="Names of specific instances from stored config (default: show all)")
    _parser.add_argument("-th", "--threads", type=int, default=THREAD_LIMIT, help="Set the number of concurrent threads to use when updating cases (default: up to ")
    _parser.add_argument("-i", "--inactive", action="store_true", help="Include inactive users in the results")

    # Add standard output arg definitions:
    #         "-f", "--file" (Also write output to a file)
    #         "-o", "--output" (Output style, e.g. table, csv, json, json-pretty)
    #         "-t", "--table_format" (for output style of table, set a specific table style, such as plain, grid, and jira)
    # Also sets logging automatically
    final_args, logger = lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_credential_file_arg=True,
        include_list_output_args=True,
        include_logging_args=True,
        default_output="table"
    )
    if final_args.threads <= 0:
        raise ValueError("Invalid thread count requested")
    return final_args, logger.log


# Must be run outside of main in order for the full effect of verbose logging
inputs, local_log = get_args()
CREDENTIALS_FILE_NAME = inputs.credentials_file_name

INSTANCE_NAMES = inputs.instance_names or lhub_cli.list_all_instances(CREDENTIALS_FILE_NAME)
if not INSTANCE_NAMES:
    raise IOError("No stored LogicHub instances found")

INSTANCE_COUNT = len(INSTANCE_NAMES)  # total count gets used so much, might as well calculate it just once
THREAD_COUNT = inputs.threads
LOG_LEVEL = inputs.LOG_LEVEL
HIDE_INACTIVE = inputs.inactive is False  # Hide inactive users, True by default

OUTPUT_COLUMNS = ["email", "is_admin", "groups", "password_enabled", "sso_enabled"]
if not HIDE_INACTIVE:
    OUTPUT_COLUMNS += ["is_enabled", "is_deleted"]

COMBINED_RESULTS = []  # Result data for final output
RUNNING_JOBS = []  # Track running jobs for smarter multithreading
INSTANCE_SESSIONS = {}  # session tracker, where instance name is the key and its lhub_cli session is the value
FINISHED = []  # Track completed jobs for the progress bar


def process_instance(name, connection_number):
    local_log.debug(f"Verifying connection {connection_number}/{INSTANCE_COUNT}", i=name)
    INSTANCE_SESSIONS[name] = lhub_cli.LogicHubCLI(
        instance_name=name,
        credentials_file_name=CREDENTIALS_FILE_NAME
    )
    local_log.debug(f"Connection verified: {connection_number}/{INSTANCE_COUNT}", i=name)

    local_log.debug(f"Fetching users from instance {connection_number}/{INSTANCE_COUNT}", i=name)
    cli = INSTANCE_SESSIONS[name]
    COMBINED_RESULTS.extend((
        cli.actions.list_users(
            print_output=False,
            show_hostname=True,
            attributes=OUTPUT_COLUMNS,
            hide_inactive=HIDE_INACTIVE,
        )
    ))
    del RUNNING_JOBS[RUNNING_JOBS.index(name)]
    FINISHED.append(name)


def process_all_instances():
    # moving all of these into a dedicated function that runs in a thread of its
    # own allows me to show progress as jobs complete instead of as they start
    threads = [threading.Thread(target=process_instance, name=INSTANCE_NAMES[n], kwargs=dict(name=INSTANCE_NAMES[n], connection_number=n + 1)) for n in range(INSTANCE_COUNT)]
    for n in range(INSTANCE_COUNT):
        while len(RUNNING_JOBS) >= THREAD_COUNT:
            pass
        RUNNING_JOBS.append(threads[n].name)
        threads[n].start()

    [thread.join() for thread in threads]


def main():
    local_log.info(f"Processing {INSTANCE_COUNT} instance{'' if INSTANCE_COUNT == 1 else 's'}", instance_count=INSTANCE_COUNT, thread_limit=THREAD_COUNT)

    cycle = range(INSTANCE_COUNT)
    if LOG_LEVEL != "DEBUG":
        cycle = progressbar.progressbar(cycle)
        print(f"Fetching users from {INSTANCE_COUNT} LogicHub servers")

    job_thread = threading.Thread(target=process_all_instances)

    for n in cycle:
        if n == 0:
            job_thread.start()
        while len(FINISHED) < n:
            pass

    job_thread.join()

    # Fix when the admin user's email field is returned as a string of "null"
    for u in COMBINED_RESULTS:
        if u['email'] == 'null':
            u['email'] = None

    print_fancy_lists(
        results=COMBINED_RESULTS,
        output_type=inputs.output,
        table_format=inputs.table_format,
        output_file=inputs.file,
        sort_order=["connection name"],

        # Enable to provide columns to keep, in order
        # ordered_headers=[],

        file_only=(True if inputs.file else False)
    )


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
