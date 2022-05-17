#!/usr/bin/env python3

import argparse
import json
import lhub_cli


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description="Create a new LogicHub user")
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    parser.add_argument("user", help="Username for the new user")
    parser.add_argument("email", help="Email address for the new user")
    return lhub_cli.common.args.finish_parser_args_with_logger_only(parser)


args = get_args()


def main():
    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(instance_name=args.instance_name)
    results = cli.actions.create_user(
        username=args.user,
        email=args.email,
        # authentication_type="password",
        # group_names=["Everyone"],
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
