#!/usr/bin/env python3

"""
Reprocess error batches one at a time, from oldest to newest
"""

import argparse
import re
import time
from math import floor
from sys import stderr

import lhub
from lhub.common.time import epoch_time_to_str
from lhub_cli.connection_manager import LogicHubConnection

# ToDo Currently this script pulls a list of ALL batches and their states in
#      order to check on the status of a batch that is being reprocessed,
#      because the API for checking a single batch's status does not yet support
#      API key auth. Revisit once this is resolved in order to make the script
#      more efficient and reduce the load on LogicHub.

# ToDo Add an option to reprocess all batches, regardless of state (perhaps based on date or something)


# Static/configurable vars
DEFAULT_BATCH_LIMIT = 100
DEBUG_ENABLED = False
STATES_TO_REPROCESS = ['error', 'canceled']

# Global variables
STATES = {
    'canceled': 'complete',
    'error': 'complete',
    'ready': 'complete',
    'skipped': 'complete',

    'executing': 'pending',
    'queued': 'pending',
    'retrying': 'pending',
    'scheduled': 'pending',
}


def get_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Process error batches one at a time")

    # Inputs expected from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    parser.add_argument("stream_id", type=int, help="Stream ID (int)")

    # Optional args:
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Mutually Exclusive Args
    limits = parser.add_mutually_exclusive_group()
    limits.add_argument("-l", "--limit", type=int, default=DEFAULT_BATCH_LIMIT, help=f"Set the maximum number of batches to reprocess (default: {DEFAULT_BATCH_LIMIT})")
    limits.add_argument("-1", dest="force_unlimited", action="store_true", help=f"No batch limit")

    # take in the arguments provided by user
    _args = parser.parse_args()
    if _args.debug:
        global DEBUG_ENABLED
        DEBUG_ENABLED = True
    return _args


def print_debug(message):
    if DEBUG_ENABLED is True:
        print(f"[DEBUG] {message}")


class Batches:
    def __init__(self, batch_list):
        for b in batch_list:
            if b['state'] not in STATES:
                raise ValueError(f"Unknown state: {b['state']}")
        self.all = sorted(batch_list, key=lambda k: k['to'])
        self.running = [b for b in self.all if STATES[b['state']] == 'pending']
        self.error = [b for b in self.all if b['state'] in STATES_TO_REPROCESS]
        self.map = {b['id']: b for b in self.all}


class LogicHubStream:
    VERIFY_SSL = True
    HTTP_TIMEOUT = 30
    TIME_BETWEEN_STATUS_CHECKS = 5
    _initial_batches = None
    __last_batch_check = None
    batches = None
    __stream_name = None

    def __init__(self, stream_id, **kwargs):
        self.stream_id = re.sub(r'\D+', '', stream_id) if isinstance(stream_id, str) else stream_id
        self.session = lhub.LogicHub(**kwargs)
        print(f"Checking status of stream \"{self.stream_name}\"")
        self.update_batches()

    @property
    def seconds_since_last_batch_check(self):
        if not self.__last_batch_check:
            return None
        return time.time() - self.__last_batch_check

    @property
    def seconds_to_sleep_before_next_batch_check(self):
        if self.seconds_since_last_batch_check is None:
            return 0
        _sec = self.TIME_BETWEEN_STATUS_CHECKS - self.seconds_since_last_batch_check
        return floor(0 if _sec < 0 else _sec)

    @property
    def stream_details(self):
        return self.session.actions.get_stream_by_id(self.stream_id)

    @property
    def stream_name(self):
        if not self.__stream_name:
            self.__stream_name = self.stream_details['name']
        return self.__stream_name

    def update_batches(self):
        time.sleep(self.seconds_to_sleep_before_next_batch_check)
        _all_batches = self.session.actions.get_batches_by_stream_id(self.stream_id)
        self.__last_batch_check = time.time()
        self.batches = Batches(_all_batches)
        if not self._initial_batches:
            self._initial_batches = self.batches.all

    def process_batch(self, batch_dict):
        # First check whether any batches are already running
        job_start = time.time()
        if self.batches.running:
            print(f"One or more batches currently executing. Waiting until the stream is idle.")
            while self.batches.running:
                print(f"    {len(self.batches.running)} batches in queue. (waited {int(time.time() - job_start)} seconds)", end='\r')
                self.update_batches()
                if not self.batches.running:
                    print()
            print("\nReady.\n")

        batch_id = int(re.sub(r'\D+', '', batch_dict['id']))
        _initial_state = batch_dict['state']
        print("ID: {batch_id} [{batch_start} - {batch_end}]".format(
            batch_id=batch_id,
            batch_start=epoch_time_to_str(batch_dict['from'] / 1000),
            batch_end=epoch_time_to_str(batch_dict['to'] / 1000)
        ))
        _ = self.session.actions.reprocess_batch(batch_id)
        job_start = time.time()
        batch_state = self.batches.map[f'batch-{batch_id}']['state']
        while True:
            previous_state = batch_state
            print(f'    Running... (state: "{batch_state}" @ {floor(time.time() - job_start)} seconds)', end="\r")
            self.update_batches()
            batch_state = self.batches.map[f'batch-{batch_id}']['state']
            if STATES[batch_state] != 'pending':
                if batch_state in STATES_TO_REPROCESS:
                    print(f'\nWARNING: Batch {batch_id} finished with state "{batch_state}"')
                    try:
                        errors = self.batches.map[f'batch-{batch_id}']['errorsAndWarnings'].get('errors', [])
                        for error in errors:
                            print(f'\nError:\n\n{error}\n')
                    except KeyError:
                        pass
                    exit(1)
                else:
                    break
            elif previous_state != batch_state:
                print()
        print(f"    Finished!  (state: \"{self.batches.map[f'batch-{batch_id}']['state']}\" @ {floor(time.time() - job_start)} seconds)      ")


def main():
    args = get_args()
    batch_limit = args.limit
    if args.force_unlimited or batch_limit < 1:
        batch_limit = 9999999
    print_debug(f"Batch limit set to {batch_limit}")

    connection = LogicHubConnection(args.instance_name)
    try:
        session = LogicHubStream(
            stream_id=args.stream_id,
            api_key=connection.credentials.api_key,
            password=connection.credentials.password,
            **connection.credentials.to_dict()
        )
    except lhub.exceptions.StreamNotFound as e:
        print(f'FAILED: {e.message}', file=stderr)
        return

    error_batches_remaining = [b for b in session.batches.error]
    initial_error_count = len(error_batches_remaining)
    if batch_limit and len(error_batches_remaining) > batch_limit:
        print(f"Limit exceeded. Grabbing only the oldest {batch_limit} batch{'' if batch_limit == 1 else 'es'} ({initial_error_count} total)")
        error_batches_remaining = error_batches_remaining[:batch_limit]
        initial_error_count = len(error_batches_remaining)
    else:
        msg = 'error batch found' if initial_error_count == 1 else 'error batches found'
        print(f"{initial_error_count or 'No'} {msg}")

    while error_batches_remaining:
        print(f"\n{args.instance_name}, Stream {args.stream_id}\nBatch {initial_error_count - len(error_batches_remaining) + 1} of {initial_error_count}")
        batch = error_batches_remaining.pop(0)
        session.process_batch(batch)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nControl-C Pressed; stopping...")
        exit(1)
