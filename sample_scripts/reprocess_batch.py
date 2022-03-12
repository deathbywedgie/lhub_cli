#!/usr/bin/env python3

"""
Reprocess batches on demand
"""

import json
import time
import argparse
import lhub
import sys

__version__ = "1.0.0"
__version_date__ = "2022-03-03"

# Static/configurable vars
DEBUG_ENABLED = False
_CONFIG_FILE = '/Users/chad/.logichub/servers.json'
_SECONDS_BETWEEN_CALLS = 0.5


def get_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Reprocess batches on demand")

    # Inputs expected from user
    parser.add_argument("instance", help="Nickname of the instance from stored config")
    parser.add_argument("batch_ids", type=int, nargs='+', help="Batch IDs")

    # Optional args:
    # parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # take in the arguments provided by user
    _args = parser.parse_args()
    # if _args.debug:
    #     global DEBUG_ENABLED
    #     DEBUG_ENABLED = True
    return _args


def print_debug(message):
    if DEBUG_ENABLED is True:
        print(f"[DEBUG] {message}")


def print_error(message):
    print(message, file=sys.stderr)


def print_failure(message):
    print_error(message)
    sys.exit(1)


def main():
    args = get_args()
    instance = args.instance
    batches = sorted(list(set(args.batch_ids)))
    with open(_CONFIG_FILE, 'r') as f:
        config_full = f.read()
        config_full = json.loads(config_full)
    aliases = {}
    for k, v in config_full.items():
        if v.get('aliases'):
            for alias in v['aliases']:
                aliases[alias] = k
    if instance in aliases:
        instance = aliases[instance]
    config = config_full.get(instance)

    try:
        assert config, f'Instance "{instance}" not in config file'
        assert 'hostname' in config, f"No hostname defined for instance {instance}"
        assert 'api_key' in config, f"No API key defined for instance {instance}"
        for x in batches:
            assert x > 0, f'Batch ID "{x}" is invalid. Batch IDs must be a positive number.'
    except AssertionError as e:
        print_failure(f'FAILED: {str(e)}')

    session = lhub.LogicHub(hostname=config['hostname'], api_key=config['api_key'])
    for n in range(len(batches)):
        batch_id = batches[n]
        if n > 0:
            time.sleep(_SECONDS_BETWEEN_CALLS)
        try:
            _ = session.actions.reprocess_batch(batch_id)
        except lhub.exceptions.LhBaseException as e:
            print_failure(f'FAILED: {str(e)}')
        print(f'Batch {batch_id} rerun on {instance}')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nControl-C Pressed; stopping...")
        exit(1)
