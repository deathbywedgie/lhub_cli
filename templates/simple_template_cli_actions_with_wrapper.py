#!/usr/bin/env python3

import argparse
import lhub_cli
import json


# available args and expected input
def get_args():
    _parser = argparse.ArgumentParser(description="Simple script for testing API calls")

    # Inputs required from user
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    final_parser, logger = lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_logging_args=True,
        default_log_level="INFO"
    )
    return final_parser, logger.log


# Must be run outside of main in order for the full effect of verbose logging
args, log = get_args()


def main():
    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(instance_name=args.instance_name)

    # Choose the CLI action to execute. Below is an example for
    result = cli.actions.list_users()
    print(json.dumps(result))


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
