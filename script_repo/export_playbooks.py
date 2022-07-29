#!/usr/bin/env python3
import sys

import lhub_cli
import argparse

EXPORT_FOLDER = "_exports"
DEFAULT_EXPORT_LIMIT = 0


def get_args():
    _parser = argparse.ArgumentParser(description="Export all playbooks from a LogicHub server")
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    # Optional args:
    _parser.add_argument("-l", "--limit", type=int, default=DEFAULT_EXPORT_LIMIT, help=f"Optional: limit the number of playbooks to export (default: {DEFAULT_EXPORT_LIMIT or 'None'})")
    _parser.add_argument("-d", "--destination", type=str, default=None, help="Optional: specify the path for exports (default: new \"_exports\" folder in the current working directory")

    final_parser, logger = lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_credential_file_arg=True,
        include_list_output_args=True,
        include_logging_args=True,
        default_log_level="INFO"
    )

    if not final_parser.limit:
        final_parser.limit = None
    return final_parser, logger.log


# Must be run outside of main in order for the full effect of verbose logging
args, log = get_args()


def main():
    session = lhub_cli.LogicHubCLI(
        credentials_file_name=args.credentials_file_name,
        instance_name=args.instance_name
    )
    successful, failures = session.actions.export_playbooks(
        args.destination if args.destination else EXPORT_FOLDER,
        limit=args.limit, return_summary=True
    )
    if not successful:
        failed_str = "One or more playbooks failed to export:\n\n"
        for k, v in failures.items():
            failed_str += f"\t{k}: {v['name']}\n"
            # for n in range(len(v["errors"])):
            e = v["errors"][0]
            _error = e.replace('\n', '\n\t\t')
            failed_str += f"\t\t{_error}\n\n"
        print(failed_str.rstrip() + '\n', file=sys.stderr)


if __name__ == "__main__":
    lhub_cli.common.shell.main_script_wrapper(main)
