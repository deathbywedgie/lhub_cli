#!/usr/bin/env python3

import argparse
import lhub_cli
from lhub import LogicHub
import json

SCRIPT_DESCRIPTION = "Simple script for testing API calls"


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)

    # Inputs required from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    # Optional args:
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    _args = parser.parse_args()
    _args.log_level = None
    if _args.debug:
        _args.log_level = "DEBUG"
    return _args


args = get_args()
config = lhub_cli.connection_manager.LogicHubConnection(args.instance_name)

session = LogicHub(
    **config.credentials.to_dict(),
    api_key=config.credentials.api_key,
    password=config.credentials.password,
    log_level=args.log_level
)

# Whatever call you want to test, put it below
# response = session.actions.get_version()
response = session.api.get_version_info()

print(json.dumps(response, indent=2))
