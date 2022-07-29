#!/usr/bin/env python3
import argparse
import sys

from lhub import exceptions as lhub_exceptions
from requests.exceptions import SSLError

from lhub_cli.common.shell import query_yes_no, main_script_wrapper
from lhub_cli.common.args import build_args_and_logger
from lhub_cli.connection_manager import LhubConfig


def get_args():
    _parser = argparse.ArgumentParser(description="Manage LogicHub CLI connections")
    _parser.add_argument("--show_secure", action="store_true", help="Optional: include passwords and API tokens in output")

    mgmt = _parser.add_mutually_exclusive_group(required=True)
    mgmt.add_argument('--show_all', action="store_true", help="Show all connections")
    mgmt.add_argument("instance_label", type=str, nargs="?", help="Label (name) for the connection")
    mgmt.add_argument('-c', '--create', metavar="instance_label", help="Create a new connection")
    mgmt.add_argument('-d', '--delete', metavar="instance_label", help="Delete an existing connection")

    connection = _parser.add_argument_group("New Connection Properties")
    connection.add_argument("-s", "--server", nargs='?', type=str, help="Optional: server hostname", default=None)
    connection.add_argument("-t", "--auth_type", nargs='?', type=str, choices=["api_key", "password"], help="Optional: connection authentication type")
    connection.add_argument("-a", "--api_key", nargs='?', type=str, help="Optional: connection API token", default=None)
    connection.add_argument("-u", "--username", nargs='?', type=str, help="Optional: connection username", default=None)
    connection.add_argument("-p", "--password", nargs='?', type=str, help="Optional: connection password", default=None)
    connection.add_argument("-n", "--no", action="store_true", help="Disable SSL verification")

    final_args, logger = build_args_and_logger(
        parser=_parser,
        include_credential_file_arg=True,
        include_logging_args=True,
    )
    return final_args, logger.log


def print_instance_details(_label, _config):
    print(f"\nLabel: {_label}")
    for k, v in _config.to_dict().items():
        if v is not None:
            print(f"{k}: {v}")
    if SHOW_SECURE:
        if _config.password:
            print(f"password: {_config.password}")
        if _config.api_key:
            print(f"api_key: {_config.api_key}")


# Must be run outside of main in order for the full effect of verbose logging
args, log = get_args()
VERIFY_SSL = args.no is False
SHOW_SECURE = args.show_secure


def main():
    config = LhubConfig(credentials_file_name=args.credentials_file_name)

    if args.delete:
        print(f"Deleting instance: {args.delete}")
        config.delete_connection(args.delete)

    elif args.create:
        print(f"Attempting to create instance: {args.create}")
        config.create_instance(
            instance_label=args.create,
            server=args.server,
            auth_type=args.auth_type,
            api_key=args.api_key,
            username=args.username,
            password=args.password,
            verify_ssl=args.no is False
        )

    elif args.show_all:
        instances = config.list_configured_instances()
        for i in instances:
            instance_config = config.get_instance(i)
            print_instance_details(i, instance_config)

    else:
        instance_config = config.get_instance(args.instance_label)
        if not instance_config:
            first_try = True
            while first_try or query_yes_no("\nTry again?"):
                first_try = False
                # ToDo Catch more errors... what if connection is refused? Times out? Something else entirely?
                try:
                    config.create_instance(args.instance_label)
                except SSLError as err:
                    print(str(err), file=sys.stderr)
                except lhub_exceptions.auth.APIAuthFailure:
                    print("API token authentication failed", file=sys.stderr)
                except lhub_exceptions.auth.PasswordAuthFailure:
                    print("Password authentication failed", file=sys.stderr)
                else:
                    exit()
        print_instance_details(args.instance_label, instance_config)


if __name__ == "__main__":
    main_script_wrapper(main)
