#!/usr/bin/env python3

import argparse
import json
import sys

from lhub.exceptions.base import LhBaseException
from requests.exceptions import HTTPError

import lhub_cli


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description="Delete a LogicHub user")

    # Inputs required from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    parser.add_argument("user", help="Username to delete")

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

try:
    results = cli.session.actions.delete_user_by_name(usernames=args.user)
except HTTPError as e:
    print(f"Failed with exception:\n{repr(e)}\n\nLast server response:\n{cli.session.api.last_response_text}", file=sys.stderr)
    sys.exit(1)
except LhBaseException as e:
    print(f"Failed with exception:\n{repr(e)}", file=sys.stderr)
    sys.exit(1)

print(json.dumps(results, indent=2))
