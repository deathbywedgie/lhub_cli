#!/usr/bin/env python3

"""
Reprocess batches on demand
"""

import argparse
import lhub
from lhub_cli import LogicHubCLI
from lhub_cli.log import generate_logger
import sys

# Static/configurable vars
LOG_LEVEL = "INFO"
_SECONDS_BETWEEN_CALLS = 0.5


def get_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Reprocess batches on demand")

    # Inputs expected from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    parser.add_argument("batch_ids", type=int, nargs='+', help="Batch IDs")

    # Optional args:
    logging = parser.add_mutually_exclusive_group()
    logging.add_argument("--level", type=str, default=LOG_LEVEL, help="Specify log level")
    logging.add_argument("--debug", action="store_true", help="Enable debug logging (shortcut)")
    logging.add_argument("-vv", "--verbose", action="store_true", help="Enable very verbose logging")

    return parser.parse_args()


args = get_args()
if args.verbose or args.debug:
    LOG_LEVEL = "DEBUG"
else:
    LOG_LEVEL = args.level

if not args.verbose:
    # Doing this first as any other log level prevents enabling debug logs for urllib3 and any other modules which use logging
    _ = generate_logger(__name__)
log = generate_logger(__name__, level=LOG_LEVEL)


def main():
    shell = LogicHubCLI(args.instance_name, log_level=LOG_LEVEL)
    try:
        shell.actions.reprocess_batches(args.batch_ids)
    except lhub.exceptions.LhBaseException as e:
        log.critical(f'FAILED: {str(e)}')
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.critical("Interrupted with Control-C")
        print("\nControl-C Pressed; stopping...")
        exit(1)
