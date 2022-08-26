#!/usr/bin/env python3

"""
List all users across one or more LogicHub instances

Additional packages required:
* progressbar
"""

import argparse

import lhub_cli
from lhub_cli.common.output import print_fancy_lists
import progressbar
import threading

# Configurable defaults
THREAD_LIMIT = 10


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
THREAD_COUNT = inputs.threads if inputs.threads < INSTANCE_COUNT else INSTANCE_COUNT
LOG_LEVEL = inputs.LOG_LEVEL
HIDE_INACTIVE = inputs.inactive is False  # Hide inactive users, True by default

OUTPUT_COLUMNS = ["email", "is_admin", "groups", "password_enabled", "sso_enabled"]
if not HIDE_INACTIVE:
    OUTPUT_COLUMNS += ["is_enabled", "is_deleted"]

COMBINED_RESULTS = []  # Result data for final output
RUNNING_JOBS = []  # Track running jobs for smarter multithreading
INSTANCE_SESSIONS = {}  # session tracker, where instance name is the key and its lhub_cli session is the value
FINISHED = []  # Track completed jobs for the progress bar


def connect_to_instance(name, connection_number):
    local_log.debug(f"Verifying connection {connection_number}/{INSTANCE_COUNT}", i=name)
    INSTANCE_SESSIONS[name] = lhub_cli.LogicHubCLI(
        instance_name=name,
        credentials_file_name=CREDENTIALS_FILE_NAME
    )
    del RUNNING_JOBS[RUNNING_JOBS.index(name)]
    FINISHED.append(name)


def process_instance(name, connection_number):
    local_log.debug(f"Fetching users from instance {connection_number}/{INSTANCE_COUNT}", i=name)
    cli = INSTANCE_SESSIONS[name]
    COMBINED_RESULTS.extend(
        cli.actions.list_users(
            print_output=False,
            show_hostname=True,
            attributes=OUTPUT_COLUMNS,
            hide_inactive=HIDE_INACTIVE,
        )
    )
    del RUNNING_JOBS[RUNNING_JOBS.index(name)]
    FINISHED.append(name)


def show_progress(progress_message):
    if LOG_LEVEL == "DEBUG":
        return
    cycle = progressbar.progressbar(range(INSTANCE_COUNT))
    print(progress_message)
    for n in cycle:
        while len(FINISHED) < n:
            pass
    FINISHED.clear()


def main():
    local_log.info(f"Processing {INSTANCE_COUNT} instance{'' if INSTANCE_COUNT == 1 else 's'}", instance_count=INSTANCE_COUNT, threads=THREAD_COUNT)

    progress_thread = threading.Thread(target=show_progress, args=["Verifying connections"])
    progress_thread.start()

    connections_needed = INSTANCE_NAMES.copy()
    threads = []
    for n in range(INSTANCE_COUNT):
        while True:
            if THREAD_COUNT == "unlimited" or len(RUNNING_JOBS) < THREAD_COUNT:
                _instance = connections_needed.pop(0)
                RUNNING_JOBS.append(_instance)
                new_thread = threading.Thread(target=connect_to_instance, kwargs=dict(name=_instance, connection_number=n+1))
                threads.append(new_thread)
                new_thread.start()
                break

    progress_thread.join()
    [thread.join() for thread in threads]

    users_needed = INSTANCE_NAMES.copy()
    threads = []

    progress_thread = threading.Thread(target=show_progress, args=["Fetching users"])
    progress_thread.start()

    cycle = range(INSTANCE_COUNT)
    for n in cycle:
        while True:
            if THREAD_COUNT == "unlimited" or len(RUNNING_JOBS) < THREAD_COUNT:
                _instance = users_needed.pop(0)
                RUNNING_JOBS.append(_instance)
                new_thread = threading.Thread(target=process_instance, kwargs=dict(name=_instance, connection_number=n+1))
                threads.append(new_thread)
                new_thread.start()
                break

    progress_thread.join()
    [thread.join() for thread in threads]

    print_fancy_lists(
        results=COMBINED_RESULTS,
        output_type=inputs.output,
        table_format=inputs.table_format,
        output_file=inputs.file,

        # Enable to provide columns to keep, in order
        # ordered_headers=[],

        # Enable to provide a list of columns for custom sorting
        # sort_order=[],

        file_only=(True if inputs.file else False)
    )


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
