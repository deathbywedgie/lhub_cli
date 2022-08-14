#!/usr/bin/env python3

import argparse
import json

import lhub_cli


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description="Simple script for testing API calls")

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

# Choose the API call or Action to execute
# Direct API calls:
#   cli.session.api
# Predefined actions for multiple calls or customized output:
#   cli.session.actions
# Examples:
#   cli.session.api.list_fields()
#   cli.session.api.list_playbooks()
#   cli.session.api.list_streams()
#   vs.
#   cli.session.actions.list_fields(map_mode="name")
#   cli.session.actions.list_playbooks(map_mode="id")
#   cli.session.actions.list_streams()

results = cli.session.api.get_version_info()
print(json.dumps(results, indent=2))
