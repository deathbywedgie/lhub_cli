#!/usr/bin/env python3
import sys

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
    parser.add_argument("-d", "--destination", type=str, default=None, help="Optional: specify the path for exports (default: new \"_exports\" folder in the current working directory")

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
    export_folder = EXPORT_FOLDER
    if args.destination:
        export_folder = args.destination
    successful, failures = session.actions.export_playbooks(export_folder, limit=args.limit, return_summary=True)
    if not successful:
        failed_str = "One or more playbooks failed to export:\n\n"
        for k, v in failures.items():
            failed_str += f"\t{k}: {v['name']}\n\n"
            # for n in range(len(v["errors"])):
            e = v["errors"][0]
            _error = e.replace('\n', '\n\t\t')
            failed_str += f"\t\t{_error}\n\n"
        print(failed_str.rstrip() + '\n', file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nControl-C Pressed; stopping...")
        exit(1)
