#!/usr/bin/env python3
import sys

from lhub_cli.connection_manager import LhubConfig
import argparse

SHOW_SECURE = False
VERIFY_SSL = None


def get_args():
    parser = argparse.ArgumentParser(description="Manage LogicHub CLI connections")

    parser.add_argument("instance_label", type=str, nargs="?", help="Label (name) for the connection")

    parser.add_argument("--show_secure", action="store_true", help="Optional: include passwords and API tokens in output", default=None)

    parser.add_argument("-s", "--server", nargs='?', type=str, help="Optional: server hostname", default=None)
    parser.add_argument("-t", "--auth_type", nargs='?', type=str, choices=["api_key", "password"], help="Optional: connection authentication type")
    parser.add_argument("-a", "--api_key", nargs='?', type=str, help="Optional: connection API token", default=None)
    parser.add_argument("-u", "--username", nargs='?', type=str, help="Optional: connection username", default=None)
    parser.add_argument("-p", "--password", nargs='?', type=str, help="Optional: connection password", default=None)

    mgmt = parser.add_mutually_exclusive_group()
    mgmt.add_argument('--show_all', action="store_true", help="Show all connections")
    mgmt.add_argument('-c', '--create', action="store_true", help="Create a new connection")
    mgmt.add_argument('-d', '--delete', action="store_true", help="Delete an existing connection")

    # Options that are mutually exclusive... i.e. can't be both verbose and quiet at the same time
    verify_ssl = parser.add_mutually_exclusive_group()
    verify_ssl.add_argument("-y", "--yes", action="store_true", help="Enable SSL verification")
    verify_ssl.add_argument("-n", "--no", action="store_true", help="Disable SSL verification")

    # if parser.show_all:
    #     parser.instance_label = "x"
    _args = parser.parse_args()

    if not _args.show_all and not _args.instance_label:
        print("instance_label is required except with '--show_all'", file=sys.stderr)
        exit(1)
    global VERIFY_SSL
    if _args.yes:
        VERIFY_SSL = True
    if _args.no:
        VERIFY_SSL = False
    return parser.parse_args()


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


def main():
    global SHOW_SECURE
    args = get_args()
    if args.show_secure:
        SHOW_SECURE = True
    config = LhubConfig()

    if args.delete:
        config.delete_connection(args.instance_label)

    elif args.create:
        config.create_instance(
            instance_label=args.instance_label,
            server=args.server,
            auth_type=args.auth_type,
            api_key=args.api_key,
            username=args.username,
            password=args.password,
            verify_ssl=VERIFY_SSL
        )

    elif args.show_all:
        instances = config.list_configured_instances()
        for i in instances:
            instance_config = config.get_instance(i)
            print_instance_details(i, instance_config)

    else:
        instance_config = config.get_instance(args.instance_label)
        if not instance_config:
            config.create_instance(args.instance_label)
            exit()
        print_instance_details(args.instance_label, instance_config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nControl-C Pressed; stopping...")
        exit(1)
