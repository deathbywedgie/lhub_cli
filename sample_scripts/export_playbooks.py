#!/usr/bin/env python3

import lhub_cli
import argparse

# ToDo Add an arg to allow the user to override the destination path
EXPORT_FOLDER = "_exports"
DEFAULT_EXPORT_LIMIT = 0


def get_args():
    parser = argparse.ArgumentParser(description="Export all playbooks from a LogicHub server")
    parser.add_argument("instance_label", type=str, help="Label (name) for the connection")

    # Optional args:
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-l", "--limit", type=int, default=DEFAULT_EXPORT_LIMIT, help=f"Optional: limit the number of playbooks to export (default: {DEFAULT_EXPORT_LIMIT or 'None'})")

    _args = parser.parse_args()
    if not _args.limit:
        _args.limit = None
    return _args


def main():
    args = get_args()
    session = lhub_cli.LogicHubCLI(
        args.instance_label,
        # ToDo Add a better arg for this... should be able to specify any level
        log_level="DEBUG" if args.debug else None
    )
    session.actions.export_flows(EXPORT_FOLDER, limit=args.limit)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nControl-C Pressed; stopping...")
        exit(1)
