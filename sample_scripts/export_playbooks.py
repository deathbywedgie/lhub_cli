#!/usr/bin/env python3

import lhub
import lhub_cli
import argparse

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


# ToDo NEXT: Modify the code below to make it work for exporting other resources instead, then add a new method for it to lhub_wrapper.py
#  * event types
#  * custom lists
#  * commands
#  * modules
#  * custom integration
#  * baselines
#  * scripts (legacy)
#  * scripts (new, used in runScript and not actually even exportable yet, IF it can even be exported yet)
#  * eventually dashboards & widgets (but not yet supported)
#  * cases? Probably not, but maybe...


# ToDo After expanding to other resource types, migrate to a proper script with argparse to handle them all with one script

def main():
    args = get_args()
    # ToDo Add a better arg for this... should be able to specify any level
    if args.debug:
        lhub.lhub.Logger.log_level = "DEBUG"

    session = lhub_cli.LogicHubCLI(args.instance_label)
    session.export_flows(EXPORT_FOLDER, limit=args.limit)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nControl-C Pressed; stopping...")
        exit(1)
