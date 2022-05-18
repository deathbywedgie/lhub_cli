#!/usr/bin/env python3

"""
Reprocess batches on demand
"""

import argparse
from lhub_cli import LogicHubCLI
from lhub_cli.common.shell import main_script_wrapper
from lhub_cli.common.args import build_args_and_logger

# Static/configurable vars
LOG_LEVEL = "INFO"
_SECONDS_BETWEEN_CALLS = 0.5


def get_args():
    # Range of available args and expected input
    _parser = argparse.ArgumentParser(description="Reprocess batches on demand")

    # Inputs expected from user
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    _parser.add_argument("batch_ids", type=int, nargs='+', help="Batch IDs")

    return build_args_and_logger(
        parser=_parser,
        include_credential_file_arg=True,
        include_logging_args=True,
        default_log_level=LOG_LEVEL,
    )


args, logger = get_args()


def main():
    cli = LogicHubCLI(args.instance_name, credentials_file_name=args.credentials_file_name)
    cli.actions.reprocess_batches(args.batch_ids)


if __name__ == "__main__":
    main_script_wrapper(main)
