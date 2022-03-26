#!/usr/bin/env python3

import argparse
import lhub_cli

SCRIPT_DESCRIPTION = "Simple script for testing API calls"


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)

    # Inputs required from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    # Optional args:
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


args = get_args()

# If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
cli = lhub_cli.LogicHubCLI(
    instance_name=args.instance_name,

    # If the --debug option was passed by the user, set log level to debug, otherwise leave it default
    log_level="DEBUG" if args.debug else None
)

# Choose the CLI action to execute. Below is an example for
result = cli.actions.list_users()
