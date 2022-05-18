#!/usr/bin/env python3

"""
Reprocess error batches one at a time, from oldest to newest
"""

import argparse
import re
import time
from math import floor
from datetime import datetime

from lhub import LogicHub

from lhub_cli.common.args import build_args_and_logger
from lhub_cli.common.shell import main_script_wrapper
from lhub_cli.connection_manager import LogicHubConnection

# Static/configurable vars
DEFAULT_LOG_LEVEL = "WARNING"
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
    _parser = argparse.ArgumentParser(description="Process error batches one at a time")

    # Inputs expected from user
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    _parser.add_argument("stream_id", type=int, help="Stream ID (INT)")

    # Optional args:
    _parser.add_argument("-l", "--limit", metavar="INT", type=int, default=None, help=f"Set the maximum number of batches to reprocess (default: None)")

    return build_args_and_logger(
        parser=_parser,
        include_logging_args=True,
        default_log_level=DEFAULT_LOG_LEVEL
    )


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
        log.debug("Initializing LogicHub session")
        self.session = LogicHub(**kwargs)
        print(f"Checking status of stream \"{self.stream_name}\"")
        print(f"\tURL: {self.session.api.url.stream_by_id.format(self.stream_id)}")
        update_logger(stream=self.stream_name)
        self.update_batches()

    @property
    def seconds_since_last_batch_check(self):
        if not self.__last_batch_check:
            return None
        return time.time() - self.__last_batch_check

    @property
    def seconds_to_sleep_before_next_batch_check(self):
        if self.seconds_since_last_batch_check is None or (seconds_remaining := self.TIME_BETWEEN_STATUS_CHECKS - self.seconds_since_last_batch_check) <= 0:
            return 0
        return seconds_remaining

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

    @property
    def error_batches(self):
        return [int(re.sub(r'\D+', '', b['id'])) for b in self.batches.error]

    def process_batch(self, batch_dict):
        # First check whether any batches are already running
        job_start = time.time()
        if self.batches.running:
            log.warning(f"One or more batches currently executing. Waiting until the stream is idle.")
            while self.batches.running:
                print(f"    {len(self.batches.running)} batches in queue. (waited {int(time.time() - job_start)} seconds)", end='\r')
                self.update_batches()
                if not self.batches.running:
                    print()
            log.info("Ready.")
            print("\nReady.\n")

        batch_id = int(re.sub(r'\D+', '', batch_dict['id']))
        _initial_state = batch_dict['state']
        batch_log = log.new(batch_id=batch_id, state=_initial_state)
        batch_log.debug(
            f"Batch reprocess requested",
            batch_start=self._epoch_time_to_str(batch_dict['from'] / 1000),
            batch_end=self._epoch_time_to_str(batch_dict['to'] / 1000)
        )
        if batch_id not in self.error_batches:
            batch_log.warning(f"Batch state changed; no longer in error state")
            return
        _ = self.session.actions.reprocess_batch(batch_id)
        job_start = time.time()
        batch_state = self.batches.map[f'batch-{batch_id}']['state']
        while True:
            previous_state = batch_state
            print(f'    Running... (state: "{batch_state}" @ {floor(time.time() - job_start)} seconds)', end="\r")
            self.update_batches()
            try:
                batch_state = self.batches.map[f'batch-{batch_id}']['state']
            except KeyError:
                batch_log.warning(f"Batch {batch_id} no longer found")
                continue
            batch_log = batch_log.new(batch_id=batch_id, state=batch_state)
            if STATES[batch_state] != 'pending':
                if batch_state in STATES_TO_REPROCESS:
                    print()
                    batch_log.warn(f'Batch finished with state "{batch_state}"')
                    try:
                        errors = self.batches.map[f'batch-{batch_id}']['errorsAndWarnings'].get('errors', [])
                        if errors:
                            print()
                            for error in errors:
                                batch_log.error(f"Error returned: {error}")
                    except KeyError:
                        pass
                    exit(1)
                else:
                    break
            elif previous_state != batch_state:
                print()
        print(f"    Finished!  (state: \"{batch_state}\" @ {floor(time.time() - job_start)} seconds)      ")
        batch_log.info(f"Batch processing finished", run_time_seconds=floor(time.time() - job_start))

    @staticmethod
    def _epoch_time_to_str(time_sec):
        dt = datetime.fromtimestamp(time_sec)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def update_logger(**kwargs):
    global log
    if not hasattr(update_logger, "kwargs"):
        update_logger.kwargs = kwargs
    update_logger.kwargs.update(kwargs)
    log = log.new(**update_logger.kwargs)


args, logger = get_args()
connection_name = args.instance_name
log = logger.log
update_logger(connection=connection_name, stream_id=args.stream_id)


def main():
    batch_limit = args.limit if args.limit and args.limit > 0 else 9999999
    log.debug(f"Batch limit set to {batch_limit}")

    connection = LogicHubConnection(connection_name)
    session = LogicHubStream(
        stream_id=args.stream_id,
        api_key=connection.credentials.api_key,
        password=connection.credentials.password,
        **connection.credentials.to_dict()
    )

    error_batches_remaining = [b for b in session.batches.error]
    initial_error_count = len(error_batches_remaining)
    if batch_limit and len(error_batches_remaining) > batch_limit:
        log.warning(f"Limit exceeded. Grabbing only the oldest {batch_limit} batch{'' if batch_limit == 1 else 'es'} ({initial_error_count} total)")
        error_batches_remaining = error_batches_remaining[:batch_limit]
        initial_error_count = len(error_batches_remaining)
    if not initial_error_count:
        log.debug("No error batches found")
        print(f"No error batches found")

    else:
        log.info(f"{initial_error_count} error batches found")
        print(f"{initial_error_count} error batches found")

    while error_batches_remaining:
        log.info("Error batches remaining", batch_number=initial_error_count - len(error_batches_remaining) + 1, total_batches=initial_error_count)
        print(f"\n{connection_name}, Stream {args.stream_id}\nBatch {initial_error_count - len(error_batches_remaining) + 1} of {initial_error_count}")
        batch = error_batches_remaining.pop(0)
        session.process_batch(batch)


if __name__ == "__main__":
    main_script_wrapper(main)
