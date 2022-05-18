#!/usr/bin/env python3

import argparse
import json
import lhub_cli


# available args and expected input
def get_args():
    _parser = argparse.ArgumentParser(description="Delete a LogicHub user")
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    _parser.add_argument("user", help="Username to delete")
    final_args, logger = lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_logging_args=True
    )
    return final_args, logger.log


# Must be run outside of main in order for the full effect of verbose logging
args, log = get_args()


def main():
    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(instance_name=args.instance_name)

    results = cli.actions.delete_user_by_name(username=args.user)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
