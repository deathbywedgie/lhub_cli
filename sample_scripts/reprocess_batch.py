#!/usr/bin/env python3

"""
Reprocess batches on demand
"""

import time
import argparse
import lhub
import lhub_cli
import sys

# Static/configurable vars
_SECONDS_BETWEEN_CALLS = 0.5


def get_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Reprocess batches on demand")

    # Inputs expected from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    parser.add_argument("batch_ids", type=int, nargs='+', help="Batch IDs")

    # Optional args:
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def main():
    args = get_args()
    log_level = None
    if args.debug:
        log_level = "DEBUG"
    batches = sorted(list(set(args.batch_ids)))
    shell = lhub_cli.LogicHubCLI(args.instance_name, log_level=log_level)
    for n in range(len(batches)):
        batch_id = batches[n]
        if n > 0:
            time.sleep(_SECONDS_BETWEEN_CALLS)
        try:
            _ = shell.session.actions.reprocess_batch(batch_id)
        except lhub.exceptions.LhBaseException as e:
            shell.log.fatal(f'FAILED: {str(e)}')
            sys.exit(1)
        print(f'Batch {batch_id} rerun on {args.instance_name}')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nControl-C Pressed; stopping...")
        exit(1)
